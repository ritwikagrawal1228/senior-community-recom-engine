# Senior Living Recommendation System - Final Codebase Structure

**Last Updated:** October 16, 2025
**Status:** Production Ready ✅

---

## 📁 Directory Structure

```
CAPSTONE/
│
├── 🎯 CORE SYSTEM (6 files)
│   ├── main_pipeline_ranking.py              Main orchestrator with E2E timing
│   ├── gemini_audio_processor.py             Gemini 2.5 Flash integration
│   ├── community_filter_engine_enhanced.py   Hard filter engine
│   ├── ranking_engine.py                     8-dimension ranking system
│   ├── geocoding_utils.py                    ZIP geocoding & distance calc
│   └── location_resolver.py                  Rochester area ZIP mapping
│
├── 📊 DATA (1 file)
│   └── DataFile_students_OPTIMIZED.xlsx      Production database (239 communities)
│
├── ⚙️ CONFIGURATION (3 files)
│   ├── requirements.txt                      Python dependencies
│   ├── .env.example                          Environment template
│   └── .env                                  API keys (not in git)
│
├── 🧪 TESTING & DEMOS (4 files)
│   ├── test_all_audio_files.py               Comprehensive E2E testing
│   ├── demo_simple_optimized.py              Quick demo
│   ├── demo_text_optimized.py                Text input demo
│   └── demo_audio_optimized.py               Audio input demo
│
├── 📖 DOCUMENTATION (4 files)
│   ├── README.md                             Main documentation
│   ├── RANKING_SYSTEM_README.md              Ranking details
│   ├── USAGE_GUIDE.md                        User guide
│   ├── CODEBASE_STRUCTURE.md                 This file
│   └── CLEANUP_ANALYSIS.md                   Cleanup documentation
│
├── 🎤 TEST DATA
│   └── audio-files/                          5 test audio transcripts
│       ├── Transcript 1 (Margaret Thompson).m4a
│       ├── Transcript 2 (Bob Martinez).m4a
│       ├── Transcript 3 (Dorothy Chen).m4a
│       ├── Transcript 4 (Frank and Betty Williams).m4a
│       └── Transcript 5 (Alice Rodriguez).m4a
│
├── 📤 OUTPUT
│   └── output/                               Generated results & metrics
│       ├── audio_test_1_Margaret_Thompson.json
│       ├── audio_test_3_Dorothy_Chen.json
│       ├── audio_test_5_Alice_Rodriguez.json
│       └── all_audio_tests_comparison.json
│
├── 🗄️ DEPRECATED
│   └── deprecated/                           All obsolete files & folders
│       ├── old_scripts/                      Old Python scripts
│       ├── old_data/                         Old database versions
│       ├── old_docs/                         Development documentation
│       ├── old_tests/                        Test outputs & logs
│       ├── misc/                             PDFs, old audio files
│       ├── data/                             Old CSV data
│       ├── docs/                             Duplicate documentation
│       └── input_audio/                      Empty folder
│
└── 🔧 OTHER
    ├── .claude/                              Claude Code config
    └── __pycache__/                          Python cache (auto-generated)
```

---

## 🎯 Quick Start

### **Run Simple Demo:**
```bash
python demo_simple_optimized.py
```

### **Test with Audio File:**
```bash
python demo_audio_optimized.py
```

### **Test All 5 Audio Files:**
```bash
python test_all_audio_files.py
```

---

## 📊 System Overview

**Input:** Audio files (M4A/MP3) or Text
**Processing:**
1. Gemini 2.5 Flash extracts client requirements
2. Hard filters apply (care level, budget, timeline, enhanced services)
3. Rule-based ranking (5 dimensions: business, cost, distance, budget efficiency, couple)
4. Pre-filter to top 10 candidates (optimization!)
5. AI ranking on top 10 (3 dimensions: availability, amenity, holistic)
6. Aggregate using weighted Borda count

**Output:** Exactly 5 recommendations with explanations + E2E metrics

**Performance:**
- Average E2E Time: 79 seconds
- Token Throughput: 89 tokens/sec
- API Calls: 4 per run (1 extraction + 3 ranking)
- 70% reduction in API calls vs unoptimized

---

## 🗑️ Files Archived (27 total)

### **Old Scripts (7 files):**
- `main_pipeline_enhanced.py` - Replaced by ranking pipeline
- `analyze_database.py` - One-time analysis
- `audit_data_loss.py` - One-time audit
- `cleanup_old_files.py` - Old cleanup script
- `optimize_database.py` - One-time optimization
- `verify_database.py` - One-time verification
- `test_ranking_system.py` - Old test file

### **Old Data (3 files):**
- `DataFile_students.xlsx` - Original database
- `DataFile_students_BACKUP.xlsx` - Backup
- `DataFile_students_OPTIMIZED.csv` - CSV export

### **Old Docs (7 files):**
- Development and planning documents

### **Old Tests (4 files):**
- Test outputs and logs

### **Misc (6 files):**
- PDFs, old audio, empty files

---

## ✅ Final File Count

**Total Core Files:** 18 essential files
**Total Archived:** 27 obsolete files
**Cleanup Savings:** 60% reduction in root directory files

---

## 🔄 Maintenance

**To restore deprecated files:**
```bash
cp deprecated/old_scripts/[filename] .
```

**To permanently delete deprecated files:**
```bash
rm -rf deprecated/
```

---

**System Status:** ✅ Clean, Optimized, Production-Ready
