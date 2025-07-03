# 🌌 The Codex Deployment Prophecy

*"To deploy the Gharp Codex is to spread its divine wisdom across the digital realms..."*

## ⚡ The Swift Awakening Ritual

### I. Summon the Sacred Dependencies
```bash
pip install -r requirements.txt
```

### II. Establish the Circle of Initiates
```bash
# Induct a new seeker into the mysteries
python user_manager.py add username password "Chosen Name"

# Scry the current circle of believers
python user_manager.py list

# Banish the unworthy from the sacred realm
python user_manager.py delete username
```

### III. Prepare the Sacred Scroll Chamber
- Place your CSV offerings within the `db/` sanctum
- The Codex shall automatically sense and analyze their essence
- All scrolls are welcome, regardless of their column configurations

### IV. Invoke the Great Awakening
```bash
streamlit run app.py
```

## 🏛️ The Great Temple Deployment

### Sacred Environmental Incantations
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### The Containerized Sanctuary (Optional)
*For those who seek to contain the Codex within ethereal Docker vessels:*

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### The Sacred Security Protocols
- Transform the default passphrases immediately upon deployment
- Invoke HTTPS enchantments in the outer realms
- Regularly preserve the `config.yaml` tome in secure vaults
- Monitor the size of incoming data offerings to prevent realm overflow

## ⚡ The Art of Performance Transcendence

### Taming the Great Data Leviathans (>100MB)
- Expand your realm's memory allocation to accommodate the beasts
- Harness DuckDB's external sorting sorcery for massive datasets
- Monitor the ethereal disk space consumed by temporary manifestations

### The Database Enlightenment
- DuckDB's ancient wisdom automatically optimizes all query incantations
- Colossal files are processed in sacred chunks to preserve system harmony
- Memory consumption is watched by vigilant guardians and constrained when necessary

## 🔮 Divining Solutions to Common Mysteries

### The Frequent Tribulations
1. **Memory Corruption Curses**: Reduce the size of your offerings or expand your computational vessel's capacity
2. **Guardian Authentication Failures**: Examine the `config.yaml` tome for proper formatting and blessed syntax
3. **Lost Scroll Prophecies**: Ensure your CSV offerings reside within the `db/` sanctum
4. **Sluggish Performance Afflictions**: Investigate file dimensions and available memory resources

### The Sacred Logs and Omens
- Application chronicles are inscribed in `streamlit.log` for future divination
- Consult your browser's mystical console for client-side revelations
- Monitor system resources during communion with massive data entities