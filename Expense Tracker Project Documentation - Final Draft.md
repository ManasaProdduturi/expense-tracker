# Expense Tracker — Project Documentation

**Project:** Expense Tracker  
**Tagline:** *Where did my money go?*  
**Course:** CS50x Final Project  
**Type:** Personal expense-tracking web application

## 1. Project Overview

Expense Tracker is a web application that helps users record, organize, search, and review their personal expenses. It provides expense-management tools and a dashboard with spending summaries and charts.

The project focuses on tracking expenses. It does not attempt to be a complete personal-finance platform.

## 2. Features

### Accounts and authentication
- User registration, login, and logout.
- Passwords are hashed before being stored.
- Session-based authentication protects pages that require a signed-in user.
- Registration and account forms include validation and user feedback.

### Expense management
- Add, view, edit, and delete expenses.
- Assign each expense to one of the predefined categories.
- Store an amount, date, category, and optional description.
- Reject invalid expense data, including non-positive amounts and future dates.

### Categories
The application provides 12 predefined categories:

- Food
- Transport
- Shopping
- Housing
- Bills & Utilities
- Entertainment
- Health
- Education
- Travel
- Subscriptions
- Personal
- Other

Custom user-created categories are not included in the current scope.

### Search and filtering
Users can search expense descriptions and filter expenses by:
- Category
- Start and end dates
- Minimum and maximum amount

Filters can be combined. Users can clear the filters to return to the complete expense list.

### Dashboard and analytics
The dashboard displays:
- Total spending
- Expense count
- Average spending
- Category-wise spending chart
- Spending-over-time chart

Dashboard results can be filtered by a supported time period, including all time, the current month, the previous month, and the current year.

### Account management
- Change the preferred currency.
- Change the account password.
- Reset a forgotten password using email one-time passcode (OTP) verification.
- Delete an account using OTP verification and a final confirmation step.

Email-based features depend on correct SMTP configuration in the environment where the application is running.

## 3. Technologies

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Flask | Web framework and routing |
| SQLite | Relational database |
| SQL | Database queries and data operations |
| HTML | Page structure |
| CSS | Application-specific styling |
| JavaScript | Client-side interactions and validation |
| Bootstrap 5 | Layout and responsive styling |
| Jinja | Server-rendered HTML templates |
| Chart.js | Dashboard charts |
| Git and GitHub | Version control and source-code hosting |
| Microsoft Azure App Service | Application hosting |

## 4. Application Structure

The application uses Flask routes to process requests, SQLite to store data, and Jinja templates to render pages. Static CSS and JavaScript files are kept separate from the templates.

The main project files and directories include:

```text
Expense-Tracker/
├── app.py
├── database.py
├── schema.sql
├── requirements.txt
├── README.md
├── templates/
├── static/
│   ├── css/
│   └── js/
└── .gitignore
```

The local virtual environment, `.env` file, and local database file are development/runtime resources and should not be committed to the public repository.

## 5. Database Design

The application uses three main SQLite tables.

### `users`
Stores account information, including a unique user ID, username, email address, and password hash.

### `categories`
Stores the predefined expense category records.

### `expenses`
Stores each expense's unique ID, owner (`user_id`), category (`category_id`), amount, date, and optional description.

### Relationships and data access
- One user can have many expenses.
- One category can be assigned to many expenses.
- Each expense belongs to a user and a category.
- Expense queries are scoped to the signed-in user's ID.
- Edit and delete operations check ownership as well as the expense ID.

The database schema is maintained in `schema.sql`. `database.py` handles database initialization and provides a reusable database connection. The schema uses repeatable setup statements so the tables and predefined categories can be initialized without manually recreating them each time.

## 6. Validation and Security

The application uses several measures to protect account and expense data:

- Passwords are stored as hashes, not plaintext.
- Session-based authentication protects signed-in pages.
- Expense queries restrict records to the current user's ID.
- Edit and delete operations check that the expense belongs to the signed-in user.
- Parameterized SQL queries are used for database operations involving submitted values.
- Server-side validation checks submitted expense and account data; browser-side validation improves usability but is not relied on as the only safeguard.
- OTP verification codes are hashed before storage and expire after 10 minutes.
- Sensitive configuration, including the Flask secret key and email settings, is supplied through environment variables rather than hard-coded into source files.
- The local `.env` file and database file should remain excluded from version control.

The login form uses a generic invalid-credentials message whether the username/email or password is incorrect. This avoids revealing whether a particular account exists, although it provides less specific feedback to the user.

## 7. Local Setup

These instructions describe the general development setup. Use the current `requirements.txt` and project files as the source of truth if they differ from this overview.

1. Install Python and Git.
2. Clone the repository and open the project directory.
3. Create and activate a virtual environment.

   ```powershell
   python -m venv venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   venv\Scripts\activate
   ```

   The execution-policy command is needed only if PowerShell blocks virtual-environment activation.

4. Install the dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

5. Configure the environment variables required by the application. Do not publish secret values. Email features require the appropriate SMTP host, port, username, password, and sender configuration.
6. Start the Flask application using the project's configured development command, for example:

   ```powershell
   python app.py
   ```

7. Open the local address printed by Flask in the terminal.

The application initializes its SQLite database through the database setup code. Never copy real credentials into documentation, screenshots, commits, or public issue reports.

## 8. Deployment

The application is deployed using Microsoft Azure App Service.

- **GitHub repository:** https://github.com/ManasaProdduturi/expense-tracker
- **Deployed application:** https://expense-tracker-dffqfghacma7cbce.centralindia-01.azurewebsites.net/

The hosted environment must have its own application settings, including the Flask secret key and SMTP configuration. Local `.env` values do not automatically become Azure App Service settings.

A successful local run does not guarantee that every feature works after deployment. The hosted version should be checked separately, especially features that depend on environment variables or email delivery.

## 9. Testing

Manual testing and review covered the application's main workflows, including:

- Registration, login, logout, and protected-page access.
- Password hashing and duplicate-account handling.
- Adding, viewing, editing, and deleting expenses.
- Expense ownership checks.
- Rejection of invalid amounts and future expense dates.
- Category display and selection.
- Description search and individual or combined filters.
- Dashboard totals, period filters, and charts.
- Currency and password changes.
- Password reset and account deletion verification flows.
- Hosted application configuration and deployment behavior.

Testing should be repeated against the latest deployed version before final submission. In particular, verify that email OTP delivery works end-to-end in the hosted environment and review the final demonstration recording to ensure important UI elements are visible.

## 10. Challenges and Solutions

### PowerShell virtual-environment activation
PowerShell initially blocked activation because of its execution policy. A process-scoped policy adjustment allowed the environment to be activated without changing the policy permanently for the machine.

### Date-variable naming conflict
During future-date validation, naming a submitted form variable `date` conflicted with Python's imported `date` class. Renaming the variable to `expense_date` resolved the conflict.

### Deployment configuration
The application initially encountered startup/configuration problems on Azure because required environment settings were missing or incorrectly configured. Reviewing the deployment logs and configuring the required App Service settings resolved the reported configuration issues.

### Hosted email OTP configuration
The forgot-password flow initially failed on Azure even though the email function was configured for local use. Azure Log Stream showed an SMTP connection error. Adding the required SMTP settings to Azure App Service configuration addressed the missing hosted configuration. The hosted flow should still be re-tested before submission.

## 11. Current Scope and Limitations

The current project is focused on personal expense tracking. It does not include:
- Bank-account integration
- Automatic transaction imports
- Investment or stock/cryptocurrency tracking
- Bill payment
- Complex budgeting or financial-planning tools
- Social features

Email-based workflows depend on the availability and correct configuration of the SMTP service. The application is a learning project and should not be treated as a substitute for a professionally audited financial service.

## 12. Possible Future Improvements

Potential improvements, if the project is extended beyond its current scope, include:
- A more polished delete-confirmation modal.
- A dedicated clear-search control for the expense filters.
- Additional accessibility and responsive-layout checks.
- More automated tests for validation, account isolation, and error cases.
- Further monitoring of hosted reliability and browser security/reputation warnings.

These are possible future enhancements, not claims that they are required for the current feature set.

## 13. Project Summary

Expense Tracker brings together account authentication, expense CRUD operations, predefined categories, search and filtering, dashboard summaries, charts, and account-management flows in a Flask application backed by SQLite. It was developed with a focused scope, version-controlled through Git/GitHub, and deployed to Azure App Service.

The project provided practical experience with web application structure, relational database design, authentication, validation, user-specific data access, debugging, environment configuration, deployment, and testing.

## 14. Final Submission Status

Before treating the CS50x submission as complete:

- [X] Re-test the deployed password-reset and account-deletion OTP flows.
- [X] Investigate and resolve any remaining browser safety/reputation warning for the deployed URL.
- [X] Review the final screen recording and ensure the category dropdown and other important UI elements are visible.
- [X] Record and upload the final demonstration video.
- [X] Add the demonstration link to the README if required by the submission plan.
- [X] Complete the official CS50x submission process and confirm it in the gradebook.
