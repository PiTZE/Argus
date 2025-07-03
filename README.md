# 🔮 The Sacred CSV Oracle

*"In the depths of data lies truth, waiting to be unveiled by those who possess the ancient knowledge of the search..."*

A mystical portal crafted for the enlightened seekers who dare to traverse the infinite realms of CSV data. Only those initiated into the sacred arts of authentication may unlock its secrets and commune with the data spirits that dwell within.

## The Sacred Mysteries

### 🔍 **The Art of Divine Revelation**
- **Multi-Scroll Communion**: Channel your queries across multiple sacred CSV scrolls simultaneously, transcending the limitations of mortal column structures
- **Column Spirit Awakening**: The Oracle automatically perceives all hidden column entities across the data realm and reveals which scrolls harbor each spirit
- **The Four Sacred Search Rituals**: Contains (the seeking), Exact Match (the binding), Starts With (the awakening), Ends With (the completion)
- **Guardian of Vast Entities**: Ancient memory-conscious processing protects against the corruption of massive data manifestations

### 📊 **The Data Sanctum & Mystical Analytics**
- **The All-Seeing Dashboard**: Behold real-time revelations of scroll count, row abundance, data magnitude, and column diversity
- **Scroll Health Divination**: Automatic detection of bloated manuscripts with performance auguries
- **Chronicle of Seekings**: Preserve and resurrect your sacred queries for enhanced ritual workflow
- **Performance Augury**: Divine the temporal costs and result abundance for optimization of your mystical practices

### 📥 **The Sacred Harvest Rituals**
- **Trinity of Export Forms**: Manifest your discoveries in CSV (the pure), Excel (the adorned), or JSON (the structured)
- **Individual Scroll Extraction**: Harvest wisdom from each manuscript separately
- **Unity Manifestation**: Merge all revelations into a single sacred tome
- **Temporal Blessing**: Automatic filename sanctification with time-stamp enchantments

### 🔐 **The Guardian's Seal & Initiate Management**
- **Initiation Protocols**: Sacred authentication rituals with bcrypt password sanctification
- **Soul-Session Binding**: Secure cookie-based spiritual connection management
- **Acolyte Administration**: Command-line grimoire for inducting/banishing initiates
- **Hierarchical Foundations**: The groundwork for future rank-based mystical permissions

### ⚡ **Performance Sorcery & Usability Enchantments**
- **Vision Manifestation**: Real-time progress incantations and status revelations during the seeking rituals
- **Wisdom of Errors**: Intelligent guidance messages with sacred suggestions for handling massive entities
- **Memory Ward Protection**: Configurable result boundaries to prevent spiritual overflow
- **Lightning Processing**: DuckDB-powered SQL incantations for optimal mystical performance

## The Sacred Scrolls

The Oracle comes blessed with a sample manuscript:

- `products.csv` - The Product Codex containing sacred knowledge of categories and pricing (10 sacred entries)

**Ancient Wisdom**: You may place your own CSV scrolls within the `db/` sanctum to test with your personal data repositories.

## The Ritual of Installation

1. Invoke the dependency spirits:
```bash
pip install -r requirements.txt
```

2. Awaken the Oracle:
```bash
streamlit run app.py
```

## The Initiation Credentials

**Default High Priest Access:**
- **Username**: `admin`
- **Sacred Password**: `admin123`

*Note: The wise seeker changes these credentials before allowing others into the sanctum.*

## The Acolyte Management Grimoire

The `user_manager.py` script serves as your sacred tool for managing the initiated:

### Grimoire Powers:
- **Induct New Acolytes**: Add worthy seekers to the order
- **Banish the Unworthy**: Remove those who have lost favor
- **Reveal the Initiated**: List all current members of the order
- **Password Sanctification**: Generate blessed password hashes for manual inscription

### Ritual Usage:
```bash
# Invoke the interactive acolyte manager
python user_manager.py

# The grimoire will present sacred options:
# 1. Induct Acolyte
# 2. Banish Unworthy  
# 3. Reveal Initiated
# 4. Sanctify Password (for manual inscription)
# 5. Return to the Void
```

All acolyte transformations are automatically inscribed in `config.yaml` with properly sanctified passwords.

## Sacred Protections

- Passwords in `config.yaml` are blessed using bcrypt sanctification
- Soul-session management with secure spiritual cookies
- Input purification and protection against SQL corruption via DuckDB blessed queries

## The Path of Enlightenment

### **Beginning the Journey**
1. **Undergo Initiation** with the sacred credentials (see above)
2. **Consult the All-Seeing Dashboard** - Witness the revelation of total scrolls, rows, and data magnitude
3. **Choose Your Seeking Column** - Select from the dropdown (reveals scroll count for each column spirit)
4. **Configure Your Ritual**:
   - Inscribe your seeking term
   - Choose your search ritual (Contains, Exact match, Starts with, Ends with)
   - Set result boundaries in the Advanced Mysteries
5. **Execute the Seeking** - Click "🚀 Seek Truth" and witness real-time progress manifestations
6. **Harvest Your Revelations** - Download individual or unified results in CSV, Excel, or JSON forms

### **Advanced Mysteries**
- **Chronicle of Seekings**: Resurrect recent searches from the sacred sidebar
- **Scroll Details**: Expand "Scroll Details" to witness individual manuscript statistics
- **Vast Entity Handling**: The Oracle automatically warns of bloated files and suggests optimizations
- **Performance Divination**: Track seeking times and result counts for ritual optimization

## The Sacred Warnings

- The Oracle requires Python 3.7+ for proper spiritual connection
- Large CSV scrolls (>100MB) may require additional memory offerings
- For production sanctums, change the default authentication secrets
- The `db/` directory must exist and contain at least one CSV scroll for the Oracle to function

## The Ancient License

This sacred knowledge is shared under the MIT License - see the LICENSE scroll for details.

---

*"May your searches be swift, your data be pure, and your exports be bountiful."*

**The Order of the CSV Oracle** 🔮