"""
create executable:
pyinstaller --onefile --name multidb main.py
"""
import json
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import readline

# Global variables
connections = {}
current_engines = []
current_sessions = []
current_db_names = []


def load_connections(file_path):
    """Load database connections from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return {db["name"]: db for db in data["databases"]}
    except Exception as e:
        print(f"Error loading connections from {file_path}: {e}")
        return {}


def connect_to_database(db_config):
    """Connect to a specific database based on its configuration using SQLAlchemy."""
    global current_engines, current_sessions, current_db_names

    # Close existing connections if any
    if current_sessions:
        for session in current_sessions:
            session.close()

    try:
        # SQLite connection
        if db_config["type"] == "sqlite":
            engine = create_engine(f"sqlite:///{db_config['connection_string']}")
        # MySQL connection using SQLAlchemy
        elif db_config["type"] == "mysql":
            #  split db_config['connection_string'] into user, password, host, database
            user, password, host, port, database = db_config['connection_string'].split(',')
            
            engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
        else:
            raise ValueError(f"Unsupported database type: {db_config['type']}")

        # Create a session and store the engine
        Session = sessionmaker(bind=engine)
        session = Session()
        current_engines.append(engine)
        current_sessions.append(session)
        current_db_names.append(db_config["name"])
        print(f"Using to {db_config['name']}.")

    except Exception as e:
        print(f"Failed to connect to {db_config['name']}: {e}")


def get_table_names():
    """Fetch and return a list of table names from the current database using SQLAlchemy."""
    if not current_sessions:
        print("No database is selected. Use the 'USE' command to select a database.")
        return []
    
    try:
        # Reflect the database schema and get the list of tables
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=current_engines[0])  # Reflect the first engine (can be adapted to reflect multiple)
        return list(metadata.tables.keys())
    except Exception as e:
        print(f"Error fetching table names: {e}")
        return []


def completer(text, state):
    """Autocomplete function for both the 'USE' command and table names."""
    buffer = readline.get_line_buffer()
    options = []

    # If buffer starts with "USE", show available connections
    if buffer.upper().startswith("USE"):
        partial = buffer[4:].strip()  # Get the part after "USE"
        options = [conn for conn in connections.keys() if conn.startswith(partial)]
    # If buffer starts with "SELECT", show available tables
    elif buffer.upper().startswith("SELECT"):
        options = get_table_names()

    if state < len(options):
        return options[state]
    return None

def reload_connections():
    """Reload the database connections from the configuration file."""
    global connections
    connections = load_connections("connections.json")
    if connections:
        print(f"Connections reloaded. Available connections: {list(connections.keys())}")
    else:
        print("No connections found or failed to reload. Please check the 'connections.json' file.")


def execute_sql_query(query, log_to_file=False, output_file="query_output.txt"):
    """Executes one or multiple SQL queries and prints the results on all selected databases."""
    if not current_sessions:
        print("No database is selected. Use the 'USE' command to select a database.")
        return

    # Split the query into multiple queries by ";"
    queries = [q.strip() for q in query.split(";") if q.strip()]  # Remove empty queries

    all_output = []

    for i, single_query in enumerate(queries, start = 1):
        # Loop over all selected databases and execute the query
        for j, session in enumerate(current_sessions):
            output = f"Connection: {current_db_names[j]}, query {i}: {single_query} -------------------------------------------------------\n"
            print(output, end="")  # Print to console
            all_output.append(output)

            try:
                # Execute the single query
                result = session.execute(text(single_query))

                # Fetch results if it's a SELECT query
                if single_query.strip().upper().startswith("SELECT"):
                    results = result.fetchall()
                    if results:
                        for row in results:
                            row_output = f"{row}\n"
                            print(row_output, end="")  # Print to console
                            all_output.append(row_output)
                    else:
                        no_rows_output = f"Query {i} executed successfully, no rows returned.\n"
                        print(no_rows_output, end="")
                        all_output.append(no_rows_output)
                else:
                    session.commit()  # Commit changes for non-SELECT queries
                    success_output = f"Query {i} executed successfully.\n"
                    print(success_output, end="")
                    all_output.append(success_output)

            except Exception as e:
                error_output = f"Error executing query {i} on {current_db_names[j]}: {e}\n"
                print(error_output, end="")
                all_output.append(error_output)

    # Log to file if enabled
    if log_to_file:
        try:
            with open(output_file, "a") as f:
                # write timestamp at the beginning of the lines
                f.writelines(all_output)
            print(f"Output written to {output_file}.")
        except Exception as e:
            print(f"Error writing output to file: {e}")


def disconnect_from_databases():
    """Disconnect from all currently selected databases."""
    global current_engines, current_sessions, current_db_names

    # Close all sessions
    if current_sessions:
        for session in current_sessions:
            session.close()
        print(f"Disconnected from {', '.join(current_db_names)}.")

    # Clear all session and engine lists
    current_engines.clear()
    current_sessions.clear()
    current_db_names.clear()


def repl():
    print("Welcome to Multi-DB REPL! 'exit' to quit.\n")
    global connections

    # Load database connections from JSON
    connections = load_connections("connections.json")

    if not connections:
        print("No connections loaded. Make sure 'connections.json' exists and is valid.")
        return

    # Debugging: Print loaded connections (optional)
    print(f"Loaded connections: {list(connections.keys())}")

    # Configure readline for autocompletion
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")  # Enable tab completion

    while True:
        try:
            # Read user input
            user_input = input(">>> ").strip()
        except EOFError:
            break

        # Exit condition
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "clear":
            print("\033[H\033[J")
            print(f"Using to: {', '.join(current_db_names) if current_db_names else 'None'}")
            continue

        if user_input.lower() == "used":
            print(f"Using to: {', '.join(current_db_names) if current_db_names else 'None'}")
            continue

        # Handle reload command to reload the connections.json file
        elif user_input.lower() == "reload":
            reload_connections()
            continue

        # Handle USE command to select a database (now it can handle multiple)
        if user_input.upper().startswith("USE"):
            args = user_input.split()
            if len(args) == 1:  # No arguments, list available connections
                print("Available connections:")
                for name in connections.keys():
                    print(f"- {name}")
            elif len(args) >= 2:  # Select multiple connections
                selected_db_names = args[1:]  # All provided names after USE command
                for db_name in selected_db_names:
                    if db_name in connections:
                        try:
                            connect_to_database(connections[db_name])
                        except Exception as e:
                            print(f"Failed to connect to {db_name}: {e}")
                    else:
                        print(f"No connection named '{db_name}' found.")
            else:
                print("Invalid USE command. Usage: USE <connection_name> [<connection_name> ...]")

        # Handle disconnect command
        elif user_input.lower() == "disconnect":
            disconnect_from_databases()

        # Handle query commands
        elif user_input.lower().startswith("query"):
            # Extract the query part after "query"
            query = user_input[5:].strip()
            if not query:
                print("Invalid query command. Usage: query <SQL statements>")
            else:
                execute_sql_query(query)

        # Handle oquery commands (log to file)
        elif user_input.lower().startswith("oquery"):
            # Extract the query part after "oquery"
            query = user_input[6:].strip()
            if not query:
                print("Invalid oquery command. Usage: oquery <SQL statements>")
            else:
                execute_sql_query(query, log_to_file=True)

        # Handle invalid commands
        else:
            print("Invalid command. Use 'USE <connection_name>' to select a database or 'query <SQL statements>' to execute queries.")

    # Clean up
    if current_sessions:
        for session in current_sessions:
            session.close()


# Run the REPL
if __name__ == "__main__":
    repl()
