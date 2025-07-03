# ☿ Deployment Guide

*"Getting this thing running shouldn't require a computer science degree."*

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Users
```bash
# Add a new user
python user_manager.py add username password "Display Name"

# List current users
python user_manager.py list

# Remove a user
python user_manager.py delete username
```

### 3. Add Your Data
- Put your CSV files in the `db/` directory
- The app will automatically detect and analyze them
- Different column structures are fine

### 4. Run the Application
```bash
streamlit run app.py
```

## ◯ Production Deployment

### Environment Variables
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Docker (Optional)
*If you're into containerization:*

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### ♄ Security Checklist
- Change the default passwords immediately
- Use HTTPS in production
- Back up your `config.yaml` file regularly
- Monitor file sizes to prevent system overload

## ⚡ Performance Optimization

### Large Files (>100MB)
- Increase system memory allocation
- Use DuckDB's external sorting for massive datasets
- Monitor disk space for temporary files

### Database Optimization
- DuckDB automatically optimizes queries
- Large files are processed in chunks
- Memory usage is monitored and limited

## ※ Troubleshooting

### Common Issues
1. **Memory errors**: Reduce file sizes or increase system memory
2. **Authentication failures**: Check `config.yaml` format and syntax
3. **Missing files**: Make sure CSV files are in the `db/` directory
4. **Slow performance**: Check file sizes and available memory

### Logs and Debugging
- Application logs are written to `streamlit.log`
- Check browser console for client-side errors
- Monitor system resources when processing large files