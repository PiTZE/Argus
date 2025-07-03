# ☿ Gharp Search - Large CSV Analytics

*"Data doesn't lie, but finding the truth requires the right incantations."*

A high-performance CSV search application designed for **very large files (2GB+ each)**. Built with enterprise-grade architecture for people who need to dig through massive CSV datasets without losing their sanity or crashing their systems.

## 🚀 **Key Features for Large Files**

### ☤ **High-Performance Search Engine**
- **Persistent DuckDB storage**: Convert CSV files once, query instantly
- **Streaming results**: Handle 2GB+ files without memory issues
- **Parallel processing**: Search multiple files simultaneously
- **Smart indexing**: Automatic indexes on searchable columns
- **Memory optimization**: 8GB+ memory limits with external sorting

### 🔍 **Advanced Search Capabilities**
- **Multi-file search**: Works across multiple CSV files with different schemas
- **Five search types**: Contains, exact match, starts with, ends with, regex
- **Chunked processing**: Stream results in configurable chunks
- **Result pagination**: Handle millions of results efficiently
- **Search caching**: Cache frequent queries for instant results

### ◯ **Data Management**
- **Dashboard**: Shows you file count, row count, data size - the basics
- **File monitoring**: Warns you when files are suspiciously large
- **Search history**: Remembers your recent searches so you don't have to
- **Performance tracking**: Times your searches because optimization matters

### ⚗ **Export Options**
- **Multiple formats**: CSV, Excel, JSON - pick your poison
- **Individual results**: Export from each file separately
- **Combined results**: Merge everything into one file
- **Timestamped files**: Automatic naming so you don't overwrite things

### ♄ **Security & Users**
- **Authentication**: Login system with bcrypt hashing (because plain text passwords are evil)
- **Session management**: Secure cookies that actually work
- **User administration**: Command-line tool for adding/removing users
- **Role foundation**: Groundwork for future permission systems

### ⚡ **Performance & UX**
- **Progress tracking**: Real-time progress bars so you know it's not frozen
- **Error handling**: Helpful error messages instead of cryptic crashes
- **Memory protection**: Configurable limits to prevent system meltdown
- **Fast processing**: DuckDB-powered SQL queries for speed

## ◇ Sample Data

Comes with one sample file:

- `products.csv` - Product catalog with categories and pricing (10 records)

**Note**: Add your own CSV files to the `db/` directory to test with real data.

## ◎ Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

3. Open `http://localhost:8501` in your browser

## ⬟ Default Credentials

**Admin access:**
- **Username**: `admin`
- **Password**: `admin123`

*Obviously change these before putting this anywhere public.*

## ♂ User Management

The `user_manager.py` script handles user administration:

### Features:
- **Add users**: Create new accounts with hashed passwords
- **Remove users**: Delete existing accounts
- **List users**: Show all current users
- **Hash passwords**: Generate bcrypt hashes for manual config editing

### Usage:
```bash
# Run the interactive user manager
python user_manager.py

# Menu options:
# 1. Add User
# 2. Remove User
# 3. List Users
# 4. Hash Password
# 5. Exit
```

All changes are automatically saved to `config.yaml` with properly hashed passwords.

## ⬢ Security

- Passwords in `config.yaml` are hashed using bcrypt
- Session management with secure cookies
- Input validation and SQL injection protection via DuckDB parameterized queries

## ◐ Usage

### **Getting Started**
1. **Login** with the default credentials (see above)
2. **Check the dashboard** - Shows total files, rows, and data size
3. **Select a column** - Choose from dropdown (shows file count for each column)
4. **Configure search**:
   - Enter your search term
   - Choose search type (Contains, Exact match, Starts with, Ends with)
   - Set result limits in Advanced Options
5. **Run search** - Click search and watch the progress bar
6. **Export results** - Download individual or combined results in CSV, Excel, or JSON

### **Advanced Features**
- **Search history**: Reuse recent searches from the sidebar
- **File details**: Expand to see individual file statistics
- **Large file handling**: Automatic warnings and optimization suggestions
- **Performance tracking**: Monitor search times and result counts

## Requirements

- Python 3.7+
- Large CSV files (>100MB) may need more memory
- Change default credentials before production use
- The `db/` directory must exist with at least one CSV file

## License

MIT License - see LICENSE file for details.

---

*"Data doesn't lie, but finding it shouldn't be painful."*