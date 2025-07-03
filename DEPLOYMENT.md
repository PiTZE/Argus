# 🚀 Deployment Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Users
```bash
# Create a new user
python user_manager.py add username password "Full Name"

# List all users
python user_manager.py list

# Delete a user
python user_manager.py delete username
```

### 3. Add Your CSV Files
- Place your CSV files in the `db/` directory
- The app will automatically detect and analyze them
- Supports files with different column structures

### 4. Run the Application
```bash
streamlit run app.py
```

## Production Deployment

### Environment Variables
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### Security Considerations
- Change default passwords immediately
- Use HTTPS in production
- Regularly backup the `config.yaml` file
- Monitor file upload sizes for large datasets

## Performance Optimization

### For Large Files (>100MB)
- Increase system memory allocation
- Consider using DuckDB's external sorting
- Monitor disk space for temporary files

### Database Optimization
- DuckDB automatically optimizes queries
- Large files are processed in chunks
- Memory usage is monitored and limited

## Troubleshooting

### Common Issues
1. **Memory errors**: Reduce file sizes or increase system memory
2. **Authentication issues**: Check `config.yaml` format
3. **File not found**: Ensure CSV files are in `db/` directory
4. **Slow performance**: Check file sizes and available memory

### Logs
- Application logs are written to `streamlit.log`
- Check browser console for client-side errors
- Monitor system resources during large file processing