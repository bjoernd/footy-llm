# Football Match Notification Service Implementation Prompts

This document contains a series of prompts for implementing the Football Match Notification Service in a test-driven, incremental manner.

## Prompt 1: Project Structure with Hatch Build System and Git Workflow

```
I'm building a Football Match Notification Service in Python that monitors matches for specific teams and sends notifications for key events. Please help me set up the initial project structure using Hatch as the build system and Git for version control.

Requirements:
1. Set up a new Python project using Hatch
2. Create a directory structure following Python best practices
3. Configure Hatch for dependency management with the following initial dependencies:
   - requests
   - pyyaml
   - pytest
   - python-dateutil
4. Set up a virtual environment using Hatch
5. Create a basic .gitignore file for Python projects
6. Initialize an empty README.md with project title and brief description
7. Configure Hatch for testing with pytest
8. Initialize a Git repository with appropriate commits

Please provide:
1. The commands to install Hatch (if not already installed)
2. Commands to initialize the project with Hatch
3. How to configure the pyproject.toml file for our dependencies and project metadata
4. How to create and activate the Hatch environment
5. The content of each initial file and the overall directory structure
6. A sequence of Git commits that build up the project incrementally, ensuring each commit:
   - Represents a logical, atomic change
   - Leaves the project in a buildable state
   - Has a clear, descriptive commit message
   - Follows Git best practices

For the Git workflow, suggest the following commits:
1. Initial commit with README and .gitignore
2. Add project structure and pyproject.toml
3. Configure Hatch environments and dependencies
4. Add initial test structure
5. Add project metadata and documentation

For each commit, provide the exact Git commands and explain what files are being committed and why.

7. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ] and add the completion timestamp in format YYYY-MM-DD HH:MM:SS
     Example: "[x] Initialize Git repository (2025-04-10 21:15:30)"
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"
```

## Prompt 2: Configuration Management with JSON and Git Workflow

```
For my Football Match Notification Service, I need to implement a configuration management system using JSON format. Please implement this with a clear Git workflow.

Requirements:
1. Create a config_manager.py module that can:
   - Load configuration from a JSON file
   - Validate the configuration structure
   - Provide access to configuration values
   - Handle missing configuration gracefully

2. The configuration should include:
   - Teams to monitor (name, league, team_id)
   - API settings (api_key, base_url, request_timeout)
   - Notification preferences (channels to use, priority order)
   - Polling settings (frequency_normal, frequency_during_match)

3. Write unit tests for the configuration manager using pytest

4. The config manager should:
   - Support default values for missing configuration
   - Validate required fields
   - Support reloading configuration at runtime
   - Provide a clean interface for accessing nested configuration values

5. Create a sample config.json file with example values

6. Implement this with the following Git commit sequence:
   - Commit 1: Add basic config_manager.py with file loading functionality
   - Commit 2: Add configuration validation logic
   - Commit 3: Implement access methods for configuration values
   - Commit 4: Add sample config.json with documentation
   - Commit 5: Write unit tests for the configuration manager

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

7. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests, ensuring it integrates well with the Hatch project structure from the previous prompt.
```

## Prompt 3: Logging System with Git Workflow

```
For my Football Match Notification Service, I need to implement a logging system that can track application events and match updates. Please implement this with a clear Git workflow.

Requirements:
1. Create a logger.py module that:
   - Sets up Python's logging module with proper configuration
   - Implements log rotation to prevent excessive disk usage
   - Provides different log levels (DEBUG, INFO, WARNING, ERROR)
   - Creates custom log levels for match events (MATCH_UPDATE, GOAL, etc.)
   - Supports structured logging for machine-readable output

2. The logger should write to:
   - Console (during development)
   - Log file (in production)
   - Separate history file for match events

3. Write unit tests for the logging functionality

4. Implement this with the following Git commit sequence:
   - Commit 1: Add basic logger setup with console output
   - Commit 2: Implement log file rotation
   - Commit 3: Add custom log levels for match events
   - Commit 4: Implement structured logging
   - Commit 5: Write unit tests for logging functionality

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests, ensuring it integrates well with the Hatch project structure from the previous prompts.
```

## Prompt 4: API Client Interface for API-Football with Git Workflow

```
For my Football Match Notification Service, I need to create an API client interface that will communicate with the API-Football.com API via RapidAPI. Please implement this with a clear Git workflow.

Requirements:
1. Create an abstract base class for API clients
2. Implement a concrete client for API-Football.com API
3. Include methods for:
   - Authenticating with the API using RapidAPI key
   - Making GET requests with proper error handling
   - Handling rate limiting
   - Processing API responses

4. The client should support:
   - Adding authentication headers for RapidAPI
   - Setting request timeouts
   - Handling HTTP errors
   - Parsing JSON responses

5. Write unit tests with mock responses

6. Implement this with the following Git commit sequence:
   - Commit 1: Create abstract API client base class
   - Commit 2: Implement API-Football client
   - Commit 3: Add authentication and request handling
   - Commit 4: Implement response processing
   - Commit 5: Write unit tests with mock responses

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

7. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ] and add the completion timestamp in format YYYY-MM-DD HH:MM:SS
     Example: "[x] Initialize Git repository (2025-04-10 21:15:30)"
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests, ensuring it integrates well with the Hatch project structure from the previous prompts.
```

## Prompt 5: Retry Mechanism with Git Workflow

```
For my Football Match Notification Service's API client, I need to implement a robust retry mechanism with exponential backoff. Please implement this with a clear Git workflow.

Requirements:
1. Create a retry decorator that can be applied to API request methods
2. Implement exponential backoff strategy with configurable parameters:
   - Initial retry delay
   - Maximum retry delay
   - Maximum number of retries
   - Jitter to prevent thundering herd problem

3. Add circuit breaker pattern to prevent repeated calls to failing endpoints
4. Handle different types of failures differently:
   - Retry on network errors and 5xx responses
   - Don't retry on 4xx errors (except 429 rate limiting)
   - Special handling for rate limiting (429) responses

5. Write unit tests for the retry mechanism

6. Implement this with the following Git commit sequence:
   - Commit 1: Add basic retry decorator
   - Commit 2: Implement exponential backoff strategy
   - Commit 3: Add circuit breaker pattern
   - Commit 4: Implement specialized error handling
   - Commit 5: Write unit tests for retry functionality

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

7. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this functionality with proper error handling and tests.
```

## Prompt 6: Data Models and Parsing for API-Football with Git Workflow

```
For my Football Match Notification Service, I need to create data models and parsing utilities for football match data from API-Football.com. Please implement this with a clear Git workflow.

Requirements:
1. Create the following data models:
   - Team (id, name, short_name, logo_url, country)
   - Match (id, home_team, away_team, start_time, status, score, competition)
   - Event (id, match_id, type, minute, team_id, player_name, description)

2. Implement a data parser that can:
   - Convert API-Football.com API responses to these models
   - Normalize data formats (dates, team names, etc.)
   - Extract relevant information from complex responses

3. Add validation for parsed data

4. Write unit tests with sample API responses

5. Implement this with the following Git commit sequence:
   - Commit 1: Create basic data model classes
   - Commit 2: Implement data validation
   - Commit 3: Add API response parsing
   - Commit 4: Implement data normalization utilities
   - Commit 5: Write unit tests for models and parsing

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

6. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ] and add the completion timestamp in format YYYY-MM-DD HH:MM:SS
     Example: "[x] Initialize Git repository (2025-04-10 21:15:30)"
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement these models and parsing utilities with proper error handling and tests.
```

## Prompt 8: Match Discovery and Tracking with API-Football and Git Workflow

```
For my Football Match Notification Service, I need to implement match discovery and tracking functionality using the API-Football.com API. Please implement this with a clear Git workflow.

Requirements:
1. Create a match_tracker.py module that can:
   - Discover upcoming matches for configured teams using API-Football
   - Track the status of discovered matches
   - Determine when to start/stop polling for a match
   - Store match information for later reference

2. The match tracker should:
   - Use the API client to fetch match schedules from API-Football
   - Filter matches for teams of interest
   - Detect new matches within the configured timeframe (e.g., 3 days)
   - Track match status changes (scheduled, in-play, finished)

3. Implement a simple storage mechanism for match data
   - Store upcoming and recent matches
   - Persist across application restarts
   - Clean up old match data

4. Write unit tests for the match tracker

5. Implement this with the following Git commit sequence:
   - Commit 1: Create match tracker structure for API-Football
   - Commit 2: Implement match discovery functionality
   - Commit 3: Add match status tracking
   - Commit 4: Implement match storage
   - Commit 5: Write unit tests for match tracking

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

6. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ] and add the completion timestamp in format YYYY-MM-DD HH:MM:SS
     Example: "[x] Initialize Git repository (2025-04-10 21:15:30)"
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

6. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 9: Event Detection with API-Football and Git Workflow

```
For my Football Match Notification Service, I need to implement event detection logic that identifies key events during matches using the API-Football.com API. Please implement this with a clear Git workflow.

Requirements:
1. Create an event_detector.py module that can:
   - Compare current match state with previous state from API-Football
   - Detect the following events:
     * Match start
     * Goals
     * Half-time
     * Match end
   - Extract match statistics when available

2. The event detector should:
   - Generate event objects for detected events
   - Include relevant context in events (score, time, etc.)
   - Avoid duplicate event detection
   - Handle missing or incomplete data gracefully

3. Write unit tests for the event detector with various match state scenarios

4. Implement this with the following Git commit sequence:
   - Commit 1: Create event detector framework for API-Football
   - Commit 2: Implement match start/end detection
   - Commit 3: Add goal detection logic
   - Commit 4: Implement half-time and statistics detection
   - Commit 5: Write unit tests for event detection

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ] and add the completion timestamp in format YYYY-MM-DD HH:MM:SS
     Example: "[x] Initialize Git repository (2025-04-10 21:15:30)"
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 11: Notification Framework with Git Workflow

```
For my Football Match Notification Service, I need to implement a notification framework that can send alerts through different channels. Please implement this with a clear Git workflow.

Requirements:
1. Create a notification_manager.py module that:
   - Manages multiple notification channels
   - Formats event information into readable messages
   - Selects appropriate channels based on configuration
   - Tracks notification delivery status

2. Create an abstract base class for notifiers with:
   - send_notification method
   - is_available method
   - get_priority method

3. The notification manager should:
   - Try channels in priority order
   - Fall back to alternative channels if primary fails
   - Avoid duplicate notifications
   - Log notification attempts and results

4. Write unit tests for the notification framework

5. Implement this with the following Git commit sequence:
   - Commit 1: Create notification manager structure
   - Commit 2: Implement abstract notifier base class
   - Commit 3: Add message formatting functionality
   - Commit 4: Implement notification delivery tracking
   - Commit 5: Write unit tests for notification framework

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

6. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 12: Email Notifier with Git Workflow

```
For my Football Match Notification Service, I need to implement an email notifier that sends match event notifications via email. Please implement this with a clear Git workflow.

Requirements:
1. Create an email_notifier.py module that:
   - Implements the abstract notifier interface
   - Connects to an SMTP server using configuration settings
   - Formats match events into readable email messages
   - Sends emails to configured recipients

2. The email notifier should:
   - Support HTML and plain text email formats
   - Include match details and event information
   - Handle connection errors gracefully
   - Track delivery status

3. Write unit tests for the email notifier

4. Implement this with the following Git commit sequence:
   - Commit 1: Create basic email notifier implementation
   - Commit 2: Add SMTP connection handling
   - Commit 3: Implement email message formatting
   - Commit 4: Add delivery status tracking
   - Commit 5: Write unit tests for email notifier

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 14: Signal Notifier with Git Workflow

```
For my Football Match Notification Service, I need to implement a Signal notifier that sends match event notifications via Signal messenger. Please implement this with a clear Git workflow.

Requirements:
1. Create a signal_notifier.py module that:
   - Implements the abstract notifier interface
   - Integrates with signal-cli for sending messages
   - Formats match events into readable Signal messages
   - Sends messages to configured Signal recipients

2. The Signal notifier should:
   - Support text formatting for readability
   - Include match details and event information
   - Handle connection errors gracefully
   - Track delivery status

3. Write unit tests for the Signal notifier

4. Implement this with the following Git commit sequence:
   - Commit 1: Create basic Signal notifier implementation
   - Commit 2: Add signal-cli integration
   - Commit 3: Implement Signal message formatting
   - Commit 4: Add delivery status tracking
   - Commit 5: Write unit tests for Signal notifier

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 15: Main Application Integration with Git Workflow

```
For my Football Match Notification Service, I need to implement the main application that integrates all components. Please implement this with a clear Git workflow.

Requirements:
1. Create a main.py module that:
   - Initializes all components (config, API client, scheduler, etc.)
   - Sets up proper dependency injection
   - Handles application lifecycle (startup, running, shutdown)
   - Processes command-line arguments

2. The main application should:
   - Load configuration from specified file
   - Initialize logging based on configuration
   - Set up API client with authentication
   - Configure scheduler with appropriate tasks
   - Handle signals for graceful shutdown
   - Implement proper error handling

3. Write integration tests for the main application flow

4. Implement this with the following Git commit sequence:
   - Commit 1: Create main application structure
   - Commit 2: Implement component initialization
   - Commit 3: Add application lifecycle management
   - Commit 4: Implement signal handling and shutdown
   - Commit 5: Write integration tests

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement this module with proper error handling and tests.
```

## Prompt 17: Documentation and README with Git Workflow

```
For my Football Match Notification Service, I need comprehensive documentation in the README.md file. Please implement this with a clear Git workflow.

Requirements:
1. Update the README.md with:
   - Detailed project description
   - Installation instructions
   - Configuration guide with examples
   - Usage instructions
   - Troubleshooting section
   - API reference for developers
   - License information

2. Include information about:
   - Supported football data sources
   - Notification channels
   - Configuration options
   - System requirements
   - Development setup

3. Add examples for common use cases

4. Implement this with the following Git commit sequence:
   - Commit 1: Create basic README structure
   - Commit 2: Add installation and configuration documentation
   - Commit 3: Document usage instructions
   - Commit 4: Add troubleshooting section
   - Commit 5: Include API reference and examples

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the documentation is accurate

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please create this documentation with clear structure and formatting.
```

## Prompt 18: Final Integration and Testing with Git Workflow

```
For my Football Match Notification Service, I need to perform final integration and testing to ensure all components work together correctly. Please implement this with a clear Git workflow.

Requirements:
1. Create integration tests that:
   - Test the full application flow with mock data
   - Verify correct interaction between components
   - Test error handling and recovery
   - Validate notification delivery

2. Implement a test harness that:
   - Simulates API responses for different scenarios
   - Mocks notification delivery
   - Verifies correct event detection
   - Tests scheduling behavior

3. Create a manual testing guide for verifying functionality

4. Implement this with the following Git commit sequence:
   - Commit 1: Create integration test framework
   - Commit 2: Implement test scenarios for core functionality
   - Commit 3: Add mock data for testing
   - Commit 4: Implement test harness for API simulation
   - Commit 5: Create manual testing guide

For each commit, provide:
- The exact Git commands
- A clear commit message
- An explanation of what's being changed and why
- Verification steps to ensure the project still builds and passes tests

5. After completing each commit, update the implementation checklist in specs/todo.md:
   - Mark completed tasks as [x] instead of [ ]
   - Add any additional tasks discovered during implementation
   - Commit the updated checklist with a message like "Update implementation checklist"

Please implement these tests and provide guidance on final integration testing.
```
