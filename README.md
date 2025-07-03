# Gharp Search - CSV Search Application

A Streamlit-based application for searching through CSV files with user authentication.

## Features

### 🔍 **Advanced Search Capabilities**
- **Multi-file Search**: Search across multiple CSV files simultaneously, even with different column structures
- **Smart Column Detection**: Automatically detects all columns across all files and shows which files contain each column
- **Multiple Search Types**: Contains, Exact match, Starts with, Ends with
- **Large File Optimization**: Efficiently handles huge CSV files with memory-conscious processing

### 📊 **Data Management & Analytics**
- **Data Overview Dashboard**: Real-time statistics showing total files, rows, size, and unique columns
- **File Health Monitoring**: Automatic detection of large files with performance warnings
- **Search History**: Track and reuse recent searches for improved workflow
- **Performance Metrics**: Search timing and result counts for optimization

### 📥 **Export & Download Options**
- **Multiple Export Formats**: CSV, Excel (.xlsx), and JSON downloads
- **Individual File Results**: Export results from each file separately
- **Combined Results**: Export all search results merged into a single file
- **Timestamped Files**: Automatic filename generation with timestamps

### 🔐 **Security & User Management**
- **User Authentication**: Secure login system with bcrypt password hashing
- **Session Management**: Secure cookie-based authentication
- **User Administration**: Command-line tool for adding/removing users
- **Role-based Access**: Foundation for future role-based permissions

### ⚡ **Performance & Usability**
- **Progress Tracking**: Real-time progress bars and status updates during searches
- **Error Handling**: Intelligent error messages with suggestions for large files
- **Memory Protection**: Configurable result limits to prevent memory issues
- **Fast Processing**: DuckDB-powered SQL queries for optimal performance

## Demo Credentials

- **Username**: `admin` | **Password**: `admin123`

## Sample Data

The application comes with a sample CSV file:

- `products.csv` - Product catalog with categories and pricing (10 records)

**Note**: You can add your own CSV files to the `db/` directory to test with your data.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Configuration

- **Authentication**: Edit `config.yaml` to modify user credentials
- **Data**: Add CSV files to the `db/` directory
- **Security**: Change the cookie key in `config.yaml` for production use

## User Management

The application includes a command-line user management tool (`user_manager.py`) for easy user administration:

```bash
python user_manager.py
```

### User Manager Features:
1. **Add User** - Create new users with hashed passwords
2. **Remove User** - Delete existing users
3. **List Users** - View all current users and their details
4. **Hash Password** - Generate bcrypt hashes for manual config editing

### Example Usage:
```bash
# Run the interactive user manager
python user_manager.py

# The tool will present a menu:
# 1. Add User
# 2. Remove User  
# 3. List Users
# 4. Hash a Password (for manual entry)
# 5. Exit
```

All user changes are automatically saved to `config.yaml` with properly hashed passwords.

## Security Notes

- Passwords in `config.yaml` are hashed using bcrypt
- Session management with secure cookies
- Input validation and SQL injection protection via DuckDB parameterized queries

## Usage

### **Getting Started**
1. **Login** with demo credentials (see above)
2. **Review Data Overview** - Check the dashboard showing total files, rows, and data size
3. **Select Search Column** - Choose from dropdown (shows file count for each column)
4. **Configure Search**:
   - Enter your search term
   - Choose search type (Contains, Exact match, Starts with, Ends with)
   - Set result limits in Advanced Options
5. **Execute Search** - Click "🚀 Search" and monitor real-time progress
6. **Export Results** - Download individual or combined results in CSV, Excel, or JSON format

### **Advanced Features**
- **Search History**: Reuse recent searches from the sidebar
- **File Details**: Expand "File Details" to see individual file statistics
- **Large File Handling**: The app automatically warns about large files and suggests optimizations
- **Performance Monitoring**: Track search times and result counts for optimization

### **Best Practices for Large Files**
- Start with smaller result limits (100-500 rows) for initial searches
- Use more specific search terms to reduce processing time
- Consider "Exact match" or "Starts with" for faster searches on large datasets
- Monitor the file size warnings in Advanced Options