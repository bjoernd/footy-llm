# Football Match Notification Service Specification

## Overview
A Python service that monitors football matches for specific teams and sends notifications for key events like goals, match start/end, and other important updates. The service will be designed to run on a Raspberry Pi and will use the api-football.com API to retrieve match data.

## Core Features

### Match Monitoring
- Monitor matches for specified teams (with primary focus on Dynamo Dresden)
- Support monitoring multiple teams and competitions simultaneously
- Treat all match types (league, cup, friendly) the same way
- Handle matches that go into extra time or penalties as regular matches that run longer
- Regularly poll for new matches and schedule changes for monitored teams

### Event Detection
- Detect and notify about match start
- Detect and notify about goals (including scorer name, current score, and match time)
- Detect and notify about match end with summary and key statistics
- Detect and notify about schedule changes (postponements, cancellations, rescheduling)
- Include mechanism to detect when a match has completed even if not explicitly indicated by API
- For penalty shootouts, send notification for every attempt with current score

### Notification System
- Send notifications via Signal
- Use minimal message formats (e.g., "Goal for TEAM. New Score: SCORE. Scorer: PLAYER NAME")
- Always include match context in notifications when monitoring multiple teams
- Send each event as a separate notification, even when events occur in quick succession
- Avoid sending duplicate notifications for the same event
- Send notifications for events even if they are reported with delay

### API Management
- Validate API credentials before starting to monitor matches
- Implement configurable daily API query limit
- Track API usage and stop polling if daily limit is reached
- Reset API query limits at midnight UTC
- No caching of API responses
- On API schema changes: log, notify user, and terminate service

### Error Handling
- On API error: retry 5 times, then skip the current event
- On network connectivity issues: retry every 30 seconds until connection is restored
- On notification failure: retry 3 times, then skip and log error
- Log all errors and major events being processed

## Technical Implementation

### Configuration
- Use a single JSON configuration file for all settings
- Configuration includes:
  - API credentials (API key for api-football.com)
  - Teams to monitor
  - Signal notification settings
  - Polling frequency
  - Daily API query limit
  - Log file location
  - Error handling settings
- Configuration changes require service restart to take effect

### Versioning and Updates
- Include version information logged on startup
- Use Python build system to create releases as Python wheels
- Updates applied on service restart

### Service Management
- Include systemd unit file for automatic startup at boot
- Health status available through `systemctl status $SERVICE`
- No notifications on service termination

### Time and Localization
- All timestamps converted to local system timezone
- All notifications and messages in English only

### Packaging and Deployment
- Package as a Python wheel for easy installation
- Installable via pip
- Use latest Python version (3.12 as of May 2025)
- Include systemd unit file for service management

### Logging
- Log to a specific log file
- Log errors and major events being processed
- Log API limit reached events and resets
- Log version information on startup

### Testing
- Use pytest as the testing framework
- Include mock objects/fixtures to simulate API responses during testing
- Set up GitHub Actions and Travis CI for continuous integration
- Use Black for code formatting and linting

### Documentation
- Use Sphinx for documentation generation
- Include README.md with:
  - Purpose of the service
  - Usage instructions
  - Configuration options
  - Examples and sample configurations
  - Information about uninstallation
  - Information about configuring for teams other than Dynamo Dresden
  - Information about modifying notification frequency/polling interval
  - Information about testing the service
  - Information about setting up as a system service
  - Information about accessing service logs
  - Information about configuring the API key
  - Information about handling API rate limiting
  - Information about configuring for different event types
  - Information about handling multiple teams simultaneously
  - Information about testing with mock data

### Dependencies
- Use latest Python version
- Manage dependencies through Python package management system

### Security
- API keys stored in configuration file
- No additional security measures required

## License
- BSD License

## Issue Reporting
- Direct users to submit GitHub issues on the project page: https://github.com/bjoernd/footy-llm
