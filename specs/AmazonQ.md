# Football Match Notification Service - Development Blueprint

## Project Overview
This document outlines the step-by-step development plan for building a Football Match Notification Service that monitors matches for specific teams and sends notifications for key events using the api-football.com API.

## Development Approach
We'll use a test-driven development approach, building the project incrementally in small, manageable steps. Each step will build upon the previous one, with comprehensive testing at every stage.

## Project Structure
```
football-notification-service/
├── src/
│   └── football_notification/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── football_api.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── match.py
│       │   ├── event.py
│       │   └── team.py
│       ├── notification/
│       │   ├── __init__.py
│       │   └── signal_notifier.py
│       ├── service/
│       │   ├── __init__.py
│       │   ├── match_monitor.py
│       │   └── event_detector.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── config_manager.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_football_api.py
│   ├── test_models.py
│   ├── test_signal_notifier.py
│   ├── test_match_monitor.py
│   ├── test_event_detector.py
│   └── test_config_manager.py
├── config.json
├── pyproject.toml
├── README.md
└── football-notification.service
```

## Development Steps

### Phase 1: Project Setup and Basic Structure

#### Step 1: Project Initialization
- Set up project structure using Hatch
- Create pyproject.toml with Hatch configuration
- Configure pytest and basic dependencies
- Set up GitHub Actions for CI

#### Step 2: Configuration Management
- Create configuration manager
- Implement JSON config file loading/validation
- Add tests for configuration handling

#### Step 3: Data Models
- Create basic data models (Match, Event, Team)
- Implement data validation and conversion
- Add tests for models

### Phase 2: API Integration

#### Step 4: Football API Client
- Create API client for api-football.com
- Implement authentication and error handling
- Add API rate limiting and tracking
- Add tests with mock responses

#### Step 5: Match Data Retrieval
- Implement match data fetching
- Add team filtering functionality
- Implement scheduled polling
- Add tests for match retrieval

### Phase 3: Event Detection and Processing

#### Step 6: Event Detection
- Implement event detection logic
- Add support for different event types (goals, match start/end)
- Create event comparison for deduplication
- Add tests for event detection

#### Step 7: Match Monitoring Service
- Create match monitoring service
- Implement polling and scheduling
- Add state management for ongoing matches
- Add tests for monitoring service

### Phase 4: Notification System

#### Step 8: Signal Notification
- Implement Signal notification client
- Create message formatting
- Add error handling and retries
- Add tests for notification sending

#### Step 9: Service Integration
- Connect all components
- Implement main service class
- Add service lifecycle management
- Add integration tests

### Phase 5: Deployment and Documentation

#### Step 10: Systemd Service
- Create systemd unit file
- Add service management scripts
- Test service startup/shutdown

#### Step 11: Documentation
- Create comprehensive README
- Add usage examples
- Document configuration options
- Add installation instructions

## Iterative Development Prompts

Below are the detailed prompts for each development step. Each prompt builds on the previous ones and includes specific instructions for test-driven development.

### Prompt 1: Project Initialization with Hatch

```
I'm building a Football Match Notification Service that monitors matches for specific teams and sends notifications for key events. Let's start by setting up the project structure using Hatch as the build system.

Please help me:

1. Create a pyproject.toml file with Hatch configuration for a project named "football_notification"
2. Set up the basic directory structure as follows:
   - src/football_notification/ (with __init__.py)
   - tests/ (with __init__.py and conftest.py)
3. Configure pytest as the testing framework
4. Set up Black for code formatting
5. Add dependencies:
   - Python 3.12
   - requests for API calls
   - pytest for testing
   - pytest-mock for mocking in tests
   - pydantic for data validation

The pyproject.toml should include proper version information, author details, and configure the package to be installable via pip. Also, create a basic README.md with the project description.

Make sure the project is set up to follow best practices for Python packaging with Hatch.
```

### Prompt 2: Configuration Management

```
Now let's implement the configuration management system for our Football Match Notification Service. We need to create a configuration manager that loads settings from a JSON file.

Please help me:

1. Create a module at src/football_notification/config/config_manager.py
2. Implement a ConfigManager class that:
   - Loads configuration from a JSON file
   - Validates required fields (API key, teams to monitor, notification settings, polling frequency)
   - Provides access to configuration values
   - Has proper error handling for missing or invalid configuration
3. Create a sample config.json file with the following structure:
   ```json
   {
     "api": {
       "key": "your_api_key_here",
       "base_url": "https://api-football.com/v3",
       "daily_limit": 100
     },
     "teams": [
       {"id": 123, "name": "Dynamo Dresden"}
     ],
     "notifications": {
       "signal": {
         "enabled": true,
         "phone_number": "+1234567890"
       }
     },
     "polling": {
       "interval_seconds": 60
     },
     "logging": {
       "file_path": "/var/log/football-notification.log",
       "level": "INFO"
     }
   }
   ```
4. Write tests in tests/test_config_manager.py that verify:
   - Configuration loading works correctly
   - Validation catches missing required fields
   - Error handling works as expected
   - Configuration values can be accessed properly

Make sure to follow best practices for configuration management and error handling.
```

### Prompt 3: Data Models

```
Let's implement the core data models for our Football Match Notification Service. We need models for teams, matches, and events.

Please help me:

1. Create the following model files:
   - src/football_notification/models/team.py
   - src/football_notification/models/match.py
   - src/football_notification/models/event.py

2. Implement the Team model with:
   - Team ID
   - Team name
   - Optional logo URL

3. Implement the Match model with:
   - Match ID
   - Home and away teams (using Team model)
   - Match status (scheduled, in-progress, completed, etc.)
   - Current score
   - Match start time
   - Competition information
   - Venue information
   - Methods to update match status and score

4. Implement the Event model with:
   - Event ID
   - Event type (enum: MATCH_START, GOAL, HALF_TIME, MATCH_END, etc.)
   - Match reference
   - Timestamp
   - Team reference (which team the event relates to)
   - Player information (for goals)
   - Current score
   - Additional event details
   - Method to format event as notification message

5. Write tests in tests/test_models.py that verify:
   - Models can be created with valid data
   - Validation rejects invalid data
   - Model methods work correctly
   - Event formatting produces correct notification messages

Use Pydantic for data validation and make sure the models handle all the data we'll need for the notification service.
```

### Prompt 4: Football API Client

```
Now let's implement the API client for interacting with the api-football.com service. This client will handle authentication, rate limiting, and fetching match data.

Please help me:

1. Create src/football_notification/api/football_api.py with a FootballApiClient class that:
   - Takes API configuration (key, base URL, daily limit)
   - Handles authentication with the API
   - Tracks API usage to respect daily limits
   - Resets usage counters at midnight UTC
   - Has methods for:
     - Fetching upcoming matches for specific teams
     - Fetching live match details
     - Fetching match events
   - Implements proper error handling for API errors
   - Has configurable retry logic (5 retries by default)

2. Write tests in tests/test_football_api.py that:
   - Mock API responses for different scenarios
   - Verify authentication works correctly
   - Test rate limiting functionality
   - Verify error handling and retry logic
   - Test the midnight UTC reset functionality
   - Ensure all API methods return properly structured data

Make sure to implement proper logging for API interactions and errors. The client should be robust against temporary API failures and should respect the daily query limits.
```

### Prompt 5: Match Data Retrieval

```
Let's build on our API client to implement match data retrieval functionality. We need to create a component that periodically fetches match data for monitored teams.

Please help me:

1. Create src/football_notification/service/match_retriever.py with a MatchRetriever class that:
   - Takes a FootballApiClient instance and configuration
   - Has methods to:
     - Fetch upcoming matches for monitored teams
     - Fetch live match details for ongoing matches
     - Filter matches by team IDs from configuration
   - Implements scheduled polling based on configuration
   - Handles API errors gracefully
   - Converts API responses to our data models (Match, Team)

2. Write tests in tests/test_match_retriever.py that:
   - Verify match filtering works correctly
   - Test scheduled polling functionality
   - Verify error handling
   - Test conversion from API responses to data models
   - Verify that matches for monitored teams are correctly identified

Make sure the match retriever respects the polling interval from configuration and handles API rate limiting appropriately.
```

### Prompt 6: Event Detection

```
Now let's implement the event detection logic. This component will compare match states between polls to detect events like goals, match start/end, etc.

Please help me:

1. Create src/football_notification/service/event_detector.py with an EventDetector class that:
   - Takes configuration settings
   - Has methods to:
     - Compare previous and current match states to detect events
     - Generate Event objects for detected changes
     - Detect different event types (match start, goals, half time, match end)
     - Handle special cases like penalty shootouts
   - Implements deduplication to avoid duplicate notifications
   - Handles delayed event reporting from the API

2. Write tests in tests/test_event_detector.py that:
   - Verify goal detection works correctly
   - Test match start/end detection
   - Verify penalty shootout handling
   - Test deduplication logic
   - Verify handling of delayed events

Make sure the event detector can handle all the event types specified in the requirements and properly generates Event objects that can be used for notifications.
```

### Prompt 7: Match Monitoring Service

```
Let's implement the match monitoring service that ties together the match retrieval and event detection components.

Please help me:

1. Create src/football_notification/service/match_monitor.py with a MatchMonitor class that:
   - Takes configuration, a FootballApiClient, and an EventDetector
   - Maintains state for ongoing matches
   - Implements the main monitoring loop:
     - Fetch upcoming matches for monitored teams
     - For each ongoing match, fetch current details
     - Use EventDetector to identify events
     - Store events for notification
     - Update match states
   - Handles scheduling of polling based on configuration
   - Implements proper error handling and logging

2. Write tests in tests/test_match_monitor.py that:
   - Verify the monitoring loop works correctly
   - Test state management for ongoing matches
   - Verify event detection integration
   - Test error handling scenarios
   - Verify scheduling works as expected

Make sure the match monitor properly integrates the match retrieval and event detection components and maintains appropriate state for ongoing matches.
```

### Prompt 8: Signal Notification

```
Now let's implement the Signal notification component that will send notifications for detected events.

Please help me:

1. Create src/football_notification/notification/signal_notifier.py with a SignalNotifier class that:
   - Takes Signal configuration (phone number, etc.)
   - Has methods to:
     - Send a notification message via Signal
     - Format events into notification messages
     - Handle notification failures with retries (3 retries by default)
   - Implements proper error handling and logging

2. Write tests in tests/test_signal_notifier.py that:
   - Verify notification formatting works correctly
   - Test retry logic for failed notifications
   - Verify error handling
   - Test different event type notifications

Since we can't actually send Signal messages in tests, make sure to use appropriate mocking. The notifier should follow the message format requirements from the specification.
```

### Prompt 9: Service Integration

```
Let's integrate all the components into a main service class that will run the football notification service.

Please help me:

1. Create src/football_notification/main.py with:
   - A NotificationService class that:
     - Takes a configuration file path
     - Initializes all components (ConfigManager, FootballApiClient, MatchRetriever, EventDetector, MatchMonitor, SignalNotifier)
     - Has methods to start and stop the service
     - Implements proper shutdown handling
     - Sets up logging based on configuration
   - A main function that:
     - Parses command line arguments
     - Initializes and starts the service
     - Handles signals for graceful shutdown

2. Write tests in tests/test_main.py that:
   - Verify service initialization works correctly
   - Test start/stop functionality
   - Verify command line argument parsing
   - Test signal handling

Make sure the main service properly integrates all components and provides a clean interface for starting and stopping the service.
```

### Prompt 10: Systemd Service

```
Let's create a systemd unit file for our service to enable automatic startup at boot.

Please help me:

1. Create a football-notification.service file with:
   - Proper systemd unit configuration
   - Dependencies on network and time synchronization
   - Automatic restart on failure
   - Appropriate user/group settings
   - Logging configuration

2. Add installation instructions to the README.md for:
   - Installing the service
   - Starting/stopping the service
   - Checking service status
   - Viewing logs

Make sure the systemd unit file follows best practices and properly manages the service lifecycle.
```

### Prompt 11: Documentation

```
Finally, let's complete the documentation for our Football Match Notification Service.

Please help me:

1. Update the README.md with comprehensive documentation including:
   - Project overview and features
   - Installation instructions
   - Configuration options with examples
   - Usage instructions
   - Troubleshooting guide
   - API rate limiting information
   - Information about configuring for different teams
   - Testing instructions
   - License information
   - Issue reporting guidelines

2. Add docstrings to all classes and methods in the codebase

Make sure the documentation is clear, comprehensive, and follows best practices for Python project documentation.
```
