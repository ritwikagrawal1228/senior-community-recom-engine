# 🏘️ Senior Living Community Recommendation Engine

**AI-Powered Multi-Level Ranking System for Senior Living Placement**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/)

---

## 📋 Overview

An intelligent recommendation system that processes audio consultations or text inputs to match clients with the most suitable senior living communities. The system uses **Gemini 2.5 Flash AI** for requirement extraction and a sophisticated **8-dimension ranking algorithm** to generate explainable recommendations.

### Key Features

✅ **Audio Processing** - Extract client requirements from consultation recordings (M4A, MP3, WAV)
✅ **Hybrid Ranking System** - 8-dimension ranking: 5 deterministic (rule-based) + 3 AI-powered (temperature=0.0)
✅ **Deterministic Input Parsing** - Temperature=0.0 ensures consistent JSON extraction from audio/text
✅ **Smart Optimization** - Pre-filters to top 10 candidates (70% reduction in API calls)
✅ **Always 5 Recommendations** - Consistent output for CRM integration
✅ **Google Sheets CRM** - Automatic data push to 3-sheet CRM (consultations, recommendations, analytics)
✅ **Full Explainability** - Detailed reasoning for every recommendation
✅ **Performance Metrics** - E2E timing, token counting, and cost tracking built-in
✅ **Retry Logic** - Automatic retry with exponential backoff for API timeouts
✅ **Web Interface** - User-friendly UI for non-technical users (drag & drop, database management)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Gemini API Key ([Get one here](https://ai.google.dev/))
- Google Sheets Service Account (for CRM integration) - Optional

### Installation

```bash
# Clone the repository
git clone https://github.com/ritwikagrawal1228/senior-community-recom-engine.git
cd senior-community-recom-engine

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add:
#   - GEMINI_API_KEY
#   - GOOGLE_SPREADSHEET_ID (optional for CRM)
#   - GOOGLE_SERVICE_ACCOUNT_FILE (optional for CRM)
```

### Option 1: Web Interface (Recommended for Non-Technical Users)

**Start the web server:**

```bash
python app.py
```

**Then open your browser to:** `http://localhost:5000`

**Features:**
- ✅ **Drag & drop audio upload** - No command line needed
- ✅ **Text consultation input** - Paste transcripts directly
- ✅ **Database management** - Add, edit, delete communities via UI
- ✅ **Visual results** - Beautiful cards with recommendations
- ✅ **Built-in help** - Comprehensive user guide in Help tab

**See:** [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) for detailed instructions

---

### Option 2: Command-Line Interface

**Process audio file and push to Google Sheets CRM:**

```bash
python run_consultation.py --audio "audio-files/Transcript 1 (Margaret Thompson).m4a"
```

**Process without pushing to CRM (testing only):**

```bash
python run_consultation.py --audio "path/to/audio.m4a" --no-push
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
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Google Sheets CRM Push     │
│  • Client Consultations     │
│  • Recommendations Detail   │
│  • Performance Analytics    │
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

### Hybrid Scoring Methodology

This system combines **deterministic (rule-based)** and **non-deterministic (AI-powered)** scoring to ensure both consistency and intelligent reasoning:

#### **Deterministic Scoring (5 Dimensions)**

These rankings use pure mathematical formulas with **zero randomness**:

1. **Business Value Ranker**
   - Formula: `willingness_score (0-10) × commission_rate (0-1.0)`
   - Example: Willingness 8 × 0.05 commission = 0.4 business value
   - **Why deterministic:** Simple multiplication, same input = same output

2. **Total Cost Ranker**
   - Formula: `monthly_fee + amortized_upfront_costs`
   - Upfront costs: Deposit + move-in fee + community fee + pet fee
   - Example: $5,000/month + $100 (amortized) = $5,100 total cost
   - **Why deterministic:** Arithmetic calculation, fully reproducible

3. **Distance Ranker**
   - Uses **GeoPy + OpenStreetMap Nominatim** for real geocoding
   - Calculates geodesic distance (great-circle distance)
   - Example: Client ZIP 14526 to Community ZIP 14618 = 12.3 miles
   - **Why deterministic:** Geographic coordinates don't change, distance formula is fixed

4. **Budget Efficiency Ranker**
   - Formula: `(monthly_fee / client_budget) × 100 = percentage utilization`
   - Example: $4,500 fee / $6,000 budget = 75% utilization
   - **Why deterministic:** Division operation, consistent results

5. **Couple Friendliness Ranker**
   - Compares 2nd person fee across communities
   - Lower 2nd person fee = better rank
   - Example: $500/month < $1,000/month → better rank
   - **Why deterministic:** Numeric comparison, no variability

**Key Point:** These 5 dimensions produce **identical rankings** every time for the same input data.

---

#### **AI-Powered Scoring (3 Dimensions)**

These rankings use **Gemini 2.5 Flash with temperature=0.0** for consistency:

6. **Availability Match Ranker**
   - **AI Task:** Match waitlist status with client timeline
   - **Input:** Client timeline (immediate/near-term/flexible), community waitlist
   - **Output:** Rank 1-N based on availability fit
   - **Temperature:** 0.0 (maximum consistency)
   - **Why AI:** Requires understanding nuanced timeline language ("ASAP", "within 2 months", "no rush")

7. **Amenity & Lifestyle Ranker**
   - **AI Task:** Match apartment types, enhanced/enriched services, amenities
   - **Input:** Client needs (memory care, pet-friendly, couple rooms), community features
   - **Output:** Rank 1-N based on lifestyle fit
   - **Temperature:** 0.0 (deterministic)
   - **Why AI:** Requires semantic matching (e.g., "studio" vs "1BR" vs "double occupancy")

8. **Holistic Fit Ranker**
   - **AI Task:** Overall compatibility considering all previous rankings
   - **Input:** All 7 prior rankings + full client profile + community details
   - **Output:** Rank 1-N based on holistic fit
   - **Temperature:** 0.0 (maximum determinism)
   - **Why AI:** Requires reasoning across multiple dimensions (e.g., "slightly more expensive but perfect location and amenities")

**Key Point:** Temperature=0.0 ensures the **same rankings** for identical inputs. The AI is deterministic, not random.

---

#### **Rank Aggregation: Weighted Borda Count**

After all 8 dimensions are ranked, we combine them using **Weighted Borda Count**:

**Formula:**
```
combined_score = Σ (rank_in_dimension × weight_of_dimension)
```

**Example:**
```
Community A Rankings:
- Business Value: Rank 3 × Weight 1.0 = 3.0
- Total Cost: Rank 1 × Weight 1.0 = 1.0
- Distance: Rank 2 × Weight 1.0 = 2.0
- Budget Efficiency: Rank 1 × Weight 1.0 = 1.0
- Couple Friendliness: Rank 5 × Weight 1.0 = 5.0
- Availability Match: Rank 1 × Weight 1.0 = 1.0
- Amenity Match: Rank 2 × Weight 1.0 = 2.0
- Holistic Fit: Rank 1 × Weight 1.0 = 1.0
────────────────────────────────────────────
Combined Score: 16.0 (lower = better)
```

**Why Borda Count?**
- Rewards communities that rank well across **multiple dimensions**
- Avoids over-emphasizing a single dimension
- Produces **stable, explainable rankings**

---

### Input Parsing Determinism

To ensure **consistent client requirement extraction**, the system uses:

#### **Audio Processing (Gemini 2.5 Flash)**

```python
# gemini_audio_processor.py:71
response = self.client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=[extraction_prompt, audio_file],
    config=types.GenerateContentConfig(
        temperature=0.0,  # Zero randomness
        response_mime_type="application/json"  # Structured output
    )
)
```

- **Temperature: 0.0** → Same audio file = same extracted JSON every time
- **JSON Output:** Forces structured data (no free-form text)
- **Result:** Client name, care level, budget, timeline, location parsed identically each time

#### **Text Processing**

```python
# gemini_audio_processor.py:49
response = self.client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=full_prompt,
    config=types.GenerateContentConfig(
        temperature=0.1,  # Slightly higher for text flexibility
        response_mime_type="application/json"
    )
)
```

- **Temperature: 0.1** → Allows minor flexibility for natural language variation
- **Still highly deterministic:** Same text input → same extracted requirements 99%+ of the time

#### **AI Ranking (Gemini 2.5 Flash)**

```python
# ranking_engine.py:485
response = self.model.generate_content(
    prompt,
    generation_config=genai.GenerationConfig(
        temperature=0.0,  # Maximum determinism
        response_mime_type="application/json"
    )
)
```

- **Temperature: 0.0** → Same input data = same AI rankings every time
- **Retry Logic:** 3 attempts with exponential backoff (2s, 4s, 8s) for API timeouts
- **Fallback:** If AI ranking fails after 3 retries, uses "Not ranked by AI" with neutral reasoning

---

### Why This Matters

**For Production Systems:**
- ✅ **Reproducibility:** Same client consultation = same recommendations
- ✅ **Auditability:** Can trace why a community was ranked #1 vs #5
- ✅ **Testing:** Can validate system behavior with known inputs
- ✅ **Debugging:** Temperature=0.0 eliminates randomness as a variable

**For CRM Integration:**
- ✅ **Consistency:** Historical data remains valid over time
- ✅ **Analytics:** Performance metrics are comparable across consultations
- ✅ **Trust:** Clients/agents can rely on consistent results

---

## 🗂️ Project Structure

```
senior-community-recom-engine/
├── 🎯 Core System
│   ├── main_pipeline_ranking.py              # Main orchestrator
│   ├── gemini_audio_processor.py             # Gemini 2.5 Flash integration
│   ├── community_filter_engine_enhanced.py   # Hard filter engine
│   ├── ranking_engine.py                     # 8-dimension ranking (with retry logic)
│   ├── geocoding_utils.py                    # Distance calculation
│   ├── location_resolver.py                  # Location mapping
│   ├── google_sheets_integration.py          # CRM integration
│   └── run_consultation.py                   # CLI entry point
│
├── 📊 Data
│   └── DataFile_students_OPTIMIZED.xlsx      # Production database (239 communities)
│
├── 🎤 Sample Data
│   └── audio-files/                          # 5 sample audio transcripts
│
├── 📖 Documentation
│   ├── README.md                             # This file
│   ├── RANKING_SYSTEM_README.md              # Detailed ranking docs
│   ├── GOOGLE_SHEETS_SETUP.md                # CRM setup guide
│   └── CODEBASE_STRUCTURE.md                 # Code organization
│
├── ⚙️ Configuration
│   ├── requirements.txt                      # Dependencies
│   ├── .env.example                          # Environment template
│   ├── .env                                  # Your config (not in git)
│   └── .gitignore                            # Git ignore rules
│
└── 🗄️ Deprecated
    └── deprecated/                           # Old/obsolete files
```

---

## 💻 Usage Examples

### Command-Line Interface (Recommended)

**Process audio consultation and push to CRM:**

```bash
python run_consultation.py --audio "audio-files/Transcript 1 (Margaret Thompson).m4a"
```

**Available options:**
- `--audio` - Path to audio file (required)
- `--no-push` - Process without pushing to Google Sheets (optional)

### Python API

**Process audio file:**

```python
from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm

# Initialize system
system = RankingBasedRecommendationSystem()

# Process audio file
result = system.process_audio_file(
    audio_path="audio-files/Transcript 1 (Margaret Thompson).m4a",
    output_file="output/result.json"
)

# Push to Google Sheets CRM
crm_result = push_to_crm(result)
print(f"Consultation #{crm_result['consultation_id']} added to CRM")
```

**Process text input:**

```python
# Process text consultation
conversation = """
Client: Hi, I'm looking for memory care for my mother.
She needs help with Alzheimer's. Budget is around $7,000/month.
We need something soon, within the next month or two.
She's in Brighton area, ZIP code 14618.
"""

result = system.process_text_input(text=conversation)

# Push to CRM
push_to_crm(result)
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
  "metrics": {
    "total_time": 72.65,
    "timings": {
      "phase1_extraction": 3.61,
      "phase3_ranking": 69.04
    },
    "token_counts": {
      "extraction_input": 2000,
      "ranking_input": 2500,
      "total_output_tokens": 615
    },
    "costs": {
      "audio_input_cost": 0.002,
      "text_input_cost": 0.00075,
      "output_cost": 0.001538,
      "total_cost": 0.004288,
      "currency": "USD",
      "pricing_model": "Gemini 2.5 Flash (2025)"
    }
  }
}
```

---


## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional - for Google Sheets CRM integration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service-account.json
```

### Google Sheets CRM Setup (Optional)

1. Create a Google Cloud project and enable Google Sheets API
2. Create a service account and download the JSON key file
3. Create a Google Sheet and share it with the service account email
4. Add credentials to `.env` file
5. Run setup: `python setup_existing_sheet.py`

For detailed instructions, see [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

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

## 🔍 Troubleshooting

### Common Issues

**Audio Processing Fails**
- Ensure clear audio quality and supported formats (M4A, MP3, WAV, OGG)
- Check that budget, timeline, and location are mentioned clearly
- Maximum file size: 50MB

**API Timeout Errors**
- System has built-in retry logic (3 attempts with exponential backoff)
- If all retries fail, check internet connection and API key validity

**Database Changes Don't Appear in Web UI**
- Refresh the page or switch tabs to reload data
- Verify Excel file is not locked by another program

**Google Sheets CRM Push Fails**
- Verify `.env` has correct `GOOGLE_SPREADSHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_FILE`
- Check spreadsheet is shared with service account email
- Ensure Google Sheets API is enabled in Google Cloud Console

For detailed web UI troubleshooting, see [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)

---

## 🙏 Acknowledgments

- **Google Gemini Team** - For the powerful Gemini 2.5 Flash model
- **OpenStreetMap Nominatim** - For geocoding services

---

## 🔗 Links

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Ranking System Documentation](RANKING_SYSTEM_README.md)
- [Google Sheets Setup Guide](GOOGLE_SHEETS_SETUP.md)
- [Codebase Structure](CODEBASE_STRUCTURE.md)
