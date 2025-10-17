# 🏘️ Senior Living Community Recommendation Engine

**AI-Powered Multi-Level Ranking System for Senior Living Placement**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Overview

An intelligent recommendation system that processes audio consultations or text inputs to match clients with the most suitable senior living communities. The system uses **Gemini 2.5 Flash AI** for requirement extraction and a sophisticated **8-dimension ranking algorithm** to generate explainable recommendations.

### Key Features

✅ **Audio Processing** - Extract client requirements from consultation recordings (M4A, MP3, WAV)
✅ **Multi-Level Ranking** - 8-dimension weighted ranking system (5 rule-based + 3 AI-powered)
✅ **Smart Optimization** - Pre-filters to top 10 candidates (70% reduction in API calls)
✅ **Always 5 Recommendations** - Consistent output for CRM integration
✅ **Full Explainability** - Detailed reasoning for every recommendation
✅ **Performance Metrics** - E2E timing and token counting built-in

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Gemini API Key ([Get one here](https://ai.google.dev/))

### Installation

```bash
# Clone the repository
git clone https://github.com/ritwikagrawal1228/senior-community-recom-engine.git
cd senior-community-recom-engine

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Run Simple Demo

```bash
python demo_simple_optimized.py
```

### Test with Audio File

```bash
python demo_audio_optimized.py
```

---

## 🏗️ System Architecture

### Workflow

```
┌─────────────┐
│ Audio/Text  │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ Gemini 2.5 Flash Extraction │
│ • Client name               │
│ • Care level needed         │
│ • Budget                    │
│ • Timeline                  │
│ • Location preference       │
│ • Special needs             │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    Hard Filters             │
│ • Care level match          │
│ • Budget compatibility      │
│ • Timeline fit              │
│ • Enhanced services         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Rule-Based Pre-Ranking      │
│ • Business value            │
│ • Cost efficiency           │
│ • Distance                  │
│ • Budget efficiency         │
│ • Couple suitability        │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Select Top 10 Candidates    │
│ (Optimization)              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ AI-Powered Ranking          │
│ (Only on Top 10)            │
│ • Availability match        │
│ • Amenity & lifestyle       │
│ • Holistic fit              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Weighted Borda Count        │
│ Rank Aggregation            │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   Top 5 Recommendations     │
│   with Explanations         │
└─────────────────────────────┘
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Average E2E Time** | 79 seconds |
| **Token Throughput** | 89 tokens/sec |
| **API Calls per Run** | 4 (1 extraction + 3 ranking) |
| **Recommendations** | Always 5 |
| **Optimization** | 70% reduction in API calls |

---

## 📊 8-Dimension Ranking System

### Rule-Based Rankings (5 dimensions)

1. **Business Value** - Commission rate × willingness to work with placement
2. **Cost Efficiency** - Total cost including upfront fees
3. **Distance** - Geographic proximity to preferred location
4. **Budget Efficiency** - How well monthly fee fits within budget
5. **Couple Suitability** - Availability of double occupancy rooms

### AI-Powered Rankings (3 dimensions)

6. **Availability Match** - Timeline compatibility (immediate/near-term/flexible)
7. **Amenity & Lifestyle** - Special needs and lifestyle preferences
8. **Holistic Fit** - Overall compatibility considering all factors

**Aggregation:** Weighted Borda count (lower combined score = better)

---

## 🗂️ Project Structure

```
senior-community-recom-engine/
├── 🎯 Core System
│   ├── main_pipeline_ranking.py              # Main orchestrator
│   ├── gemini_audio_processor.py             # Gemini 2.5 Flash integration
│   ├── community_filter_engine_enhanced.py   # Hard filter engine
│   ├── ranking_engine.py                     # 8-dimension ranking
│   ├── geocoding_utils.py                    # Distance calculation
│   └── location_resolver.py                  # Location mapping
│
├── 📊 Data
│   └── DataFile_students_OPTIMIZED.xlsx      # Production database (239 communities)
│
├── 🧪 Testing & Demos
│   ├── test_all_audio_files.py               # Comprehensive testing
│   ├── demo_simple_optimized.py              # Quick demo
│   ├── demo_text_optimized.py                # Text input demo
│   └── demo_audio_optimized.py               # Audio input demo
│
├── 🎤 Test Data
│   └── audio-files/                          # 5 sample audio transcripts
│
├── 📖 Documentation
│   ├── README.md                             # This file
│   ├── RANKING_SYSTEM_README.md              # Detailed ranking docs
│   ├── USAGE_GUIDE.md                        # User guide
│   └── CODEBASE_STRUCTURE.md                 # Code organization
│
└── ⚙️ Configuration
    ├── requirements.txt                      # Dependencies
    ├── .env.example                          # Environment template
    └── .gitignore                            # Git ignore rules
```

---

## 💻 Usage Examples

### Process Audio File

```python
from main_pipeline_ranking import RankingBasedRecommendationSystem

# Initialize system
system = RankingBasedRecommendationSystem(
    data_file_path="DataFile_students_OPTIMIZED.xlsx"
)

# Process audio file
result = system.process_audio_file(
    audio_path="audio-files/Transcript 1 (Margaret Thompson).m4a",
    output_file="output/result.json"
)

# Access results
print(f"Top recommendation: {result['recommendations'][0]['community_name']}")
print(f"E2E Time: {result['performance_metrics']['timings']['e2e_total']:.2f}s")
```

### Process Text Input

```python
# Process text consultation
conversation = """
Client: Hi, I'm looking for memory care for my mother.
She needs help with Alzheimer's. Budget is around $7,000/month.
We need something soon, within the next month or two.
She's in Brighton area, ZIP code 14618.
"""

result = system.process_text_input(
    text=conversation,
    output_file="output/text_result.json"
)
```

---

## 📈 Output Format

### JSON Structure

```json
{
  "client_info": {
    "client_name": "Margaret Thompson",
    "care_level": "Assisted Living",
    "budget": 5500,
    "timeline": "immediate",
    "location_preference": "14526"
  },
  "recommendations": [
    {
      "final_rank": 1,
      "community_id": 31,
      "community_name": "Community 31",
      "combined_rank_score": 37.0,
      "key_metrics": {
        "monthly_fee": 3528.0,
        "distance_miles": 3.83,
        "est_waitlist": "Available"
      },
      "rankings": {
        "business_rank": 5,
        "total_cost_rank": 3,
        "distance_rank": 2,
        "availability_rank": 1,
        "holistic_rank": 1
      },
      "explanations": {
        "holistic_reason": "Great option: Good cost ($3,528/month) and immediately available, well within budget."
      }
    }
  ],
  "performance_metrics": {
    "timings": {
      "e2e_total": 72.65,
      "phase1_extraction": 3.61,
      "phase3_ranking": 69.04
    },
    "token_counts": {
      "total_tokens": 5115
    }
  }
}
```

---

## 🧪 Testing

### Run All Audio Tests

```bash
python test_all_audio_files.py
```

This will:
- Test all 5 audio files sequentially
- Add 2-minute breaks between tests (API rate limiting)
- Generate comprehensive performance comparison
- Save individual results to `output/` folder

### Expected Output

```
================================================================================
PERFORMANCE COMPARISON ACROSS ALL TESTS
================================================================================

Test   Client Name                    E2E Time     Tokens     Throughput   Recs
--------------------------------------------------------------------------------
1      Margaret Thompson                 72.65s       5,115        70 t/s     5
3      Dorothy Chen                     118.15s      10,874        92 t/s     5
5      Alice Rodriguez                   40.08s       3,415        91 t/s     4
--------------------------------------------------------------------------------
AVG                                      76.96s       6,468        84 t/s
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

### Ranking Weights (Optional)

Customize ranking weights in `main_pipeline_ranking.py`:

```python
custom_weights = {
    'business': 1.5,      # Increase business priority
    'cost': 1.0,
    'distance': 0.8,      # Reduce distance importance
    'availability': 1.2,
    'budget_efficiency': 1.0,
    'couple': 1.0,
    'amenity': 1.0,
    'holistic': 1.0
}

system = RankingBasedRecommendationSystem(
    ranking_weights=custom_weights
)
```

---

## 📊 Database Schema

### Required Columns

| Column | Type | Description |
|--------|------|-------------|
| CommunityID | int | Unique identifier |
| Care Level | string | Independent/Assisted/Memory Care |
| Monthly Fee | float | Base monthly rate |
| ZIP | string | 5-digit ZIP code |
| Work with Placement? | bool | Accepts placement referrals |
| Contract Rate | float | Commission percentage |
| Est. Waitlist | string | Availability status |
| Enhanced | bool | Enhanced services available |
| Enriched | bool | Enriched programming available |

### Optimized Columns (Auto-Generated)

- `apartment_type_category` - Standardized apartment types
- `availability_score` - Numeric availability (0-99)
- `willingness_score` - Placement willingness (0-10)
- `monthly_fee_numeric` - Clean numeric fee
- `enhanced_bool` / `enriched_bool` - Boolean flags

---

## 🚨 API Limits

### Gemini Free Tier

- **Limit:** 50 requests per day
- **Rate:** 2 requests per minute (recommended)
- **Workaround:** Script includes 2-minute breaks between tests

### Upgrading

For production use, consider upgrading to paid tier:
- Visit: https://ai.google.dev/gemini-api/docs/rate-limits
- Higher quotas available

---

## 🔍 Troubleshooting

### Error: "429 RESOURCE_EXHAUSTED"

**Cause:** Daily API quota exceeded (50 requests/day on free tier)
**Solution:** Wait 24 hours for quota reset or upgrade to paid tier

### Error: "503 UNAVAILABLE"

**Cause:** Gemini API temporarily overloaded
**Solution:** Retry after 30 seconds (auto-handled by SDK)

### Error: "Budget is None"

**Cause:** Gemini failed to extract budget from audio
**Solution:** Ensure audio clearly mentions budget, or set default budget

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini Team** - For the powerful Gemini 2.5 Flash model
- **OpenStreetMap Nominatim** - For geocoding services
- **Claude AI** - For development assistance

---

## 📧 Contact

**Ritwik Agrawal**
GitHub: [@ritwikagrawal1228](https://github.com/ritwikagrawal1228)
Repository: [senior-community-recom-engine](https://github.com/ritwikagrawal1228/senior-community-recom-engine)

---

## 🔗 Links

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Project Documentation](RANKING_SYSTEM_README.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Codebase Structure](CODEBASE_STRUCTURE.md)

---

**⭐ If you find this project helpful, please consider giving it a star!**
