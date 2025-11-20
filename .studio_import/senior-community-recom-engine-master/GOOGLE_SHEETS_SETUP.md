# Google Sheets Integration Setup Guide

## 📊 Google Sheet Design

### **Sheet 1: Client Consultations**
This sheet tracks each consultation/request and overall metrics.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| **Consultation_ID** | Auto-increment | Unique ID for each request | 1, 2, 3... |
| **Timestamp** | DateTime | When processed | 2025-10-16 19:19:03 |
| **Client_Name** | Text | Client name | Margaret Thompson |
| **Care_Level** | Dropdown | Type of care needed | Assisted Living, Memory Care, Independent Living |
| **Budget** | Currency | Monthly budget | $5,500 |
| **Timeline** | Dropdown | Move-in urgency | immediate, near-term, flexible |
| **Location_ZIP** | Text | Preferred ZIP code | 14526 |
| **Special_Needs** | Text | Additional requirements | Pets: No, Enhanced services needed |
| **Total_Recommendations** | Number | Number of matches | 5 |
| **Top_Community_ID** | Number | Best match ID | 31 |
| **Top_Community_Name** | Text | Best match name | Community 31 |
| **Top_Monthly_Fee** | Currency | Best match fee | $3,528 |
| **Top_Distance** | Number | Best match distance | 3.83 miles |
| **Top_Score** | Number | Combined rank score | 37.0 |
| **Top_Reason** | Text | Why this is best | Great option: Good cost and immediately available |
| **Processing_Time** | Number | E2E time in seconds | 72.65 |
| **Total_Cost** | Currency | API cost | $0.004770 |
| **Status** | Dropdown | Follow-up status | New, Contacted, Tours Scheduled, Placed, Lost |
| **Assigned_To** | Text | Staff member | John Smith |
| **Notes** | Text | Additional notes | Called client, scheduled tour for Thursday |

---

### **Sheet 2: Recommendations Detail**
This sheet stores ALL recommendations (up to 5 per consultation).

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| **Consultation_ID** | Number | Links to Sheet 1 | 1 |
| **Client_Name** | Text | For reference | Margaret Thompson |
| **Rank** | Number | Recommendation rank | 1, 2, 3, 4, 5 |
| **Community_ID** | Number | Community identifier | 31 |
| **Community_Name** | Text | Community name | Community 31 |
| **Monthly_Fee** | Currency | Base monthly rate | $3,528 |
| **Distance_Miles** | Number | Distance from client | 3.83 |
| **Availability** | Text | Waitlist status | Available, 1-2 months, Unconfirmed |
| **Combined_Score** | Number | Final rank score | 37.0 |
| **Business_Rank** | Number | Business dimension rank | 4 |
| **Cost_Rank** | Number | Cost dimension rank | 6 |
| **Distance_Rank** | Number | Distance dimension rank | 2 |
| **Availability_Rank** | Number | Availability dimension rank | 1 |
| **Holistic_Reason** | Text | AI explanation | Great option: Good cost and immediately available |
| **Contract_Rate** | Text | Commission % | 100% |
| **Work_With_Placement** | Text | Accepts referrals | Yes, No |
| **Tour_Scheduled** | Date | Tour date | 2025-10-20 |
| **Tour_Status** | Dropdown | Tour outcome | Pending, Completed, Cancelled |
| **Client_Feedback** | Text | Client reaction | Loved the amenities, concerned about distance |

---

### **Sheet 3: Performance Analytics**
This sheet tracks system performance over time.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| **Date** | Date | Processing date | 2025-10-16 |
| **Consultation_ID** | Number | Links to Sheet 1 | 1 |
| **Processing_Time_Seconds** | Number | E2E time | 72.65 |
| **Audio_Input_Tokens** | Number | Audio tokens used | 2,000 |
| **Text_Input_Tokens** | Number | Text tokens used | 2,400 |
| **Output_Tokens** | Number | Output tokens used | 715 |
| **Total_Tokens** | Number | All tokens | 5,115 |
| **API_Calls** | Number | Gemini calls made | 4 |
| **Audio_Input_Cost** | Currency | Audio cost | $0.002000 |
| **Text_Input_Cost** | Currency | Text cost | $0.000720 |
| **Output_Cost** | Currency | Output cost | $0.001788 |
| **Total_Cost** | Currency | Total API cost | $0.004508 |
| **Throughput_Tokens_Per_Sec** | Number | Processing speed | 70 |
| **Communities_Filtered** | Number | Passed hard filters | 12 |
| **Communities_Ranked** | Number | AI ranked | 10 |

---

## 🔧 Setup Instructions

### **Step 1: Create Google Sheet**

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it: **"Senior Living CRM - Recommendations"**
4. Create 3 sheets (tabs):
   - Sheet 1: "Client Consultations"
   - Sheet 2: "Recommendations Detail"
   - Sheet 3: "Performance Analytics"

### **Step 2: Set Up Column Headers**

Copy the column names from the tables above into Row 1 of each sheet.

**Optional: Add Data Validation**
- Care_Level: Independent Living, Assisted Living, Memory Care
- Timeline: immediate, near-term, flexible
- Status: New, Contacted, Tours Scheduled, Placed, Lost
- Tour_Status: Pending, Completed, Cancelled

### **Step 3: Enable Google Sheets API**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Sheets API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Enable **Google Drive API** (required for file access):
   - Same process as above

### **Step 4: Create Service Account**

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in details:
   - **Name:** Senior Living Recommendation System
   - **Description:** API service account for CRM integration
4. Click "Create and Continue"
5. Grant role: **Editor** (or create custom role)
6. Click "Done"

### **Step 5: Generate JSON Key**

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose **JSON** format
5. Click "Create"
6. **Save the downloaded JSON file** as `service_account.json` in your project folder

### **Step 6: Share Google Sheet with Service Account**

1. Open your Google Sheet
2. Click "Share" button
3. Copy the **service account email** from the JSON file:
   - It looks like: `your-service-account@your-project.iam.gserviceaccount.com`
4. Paste it in the "Share with people and groups" field
5. Set permission to **Editor**
6. Click "Send" (uncheck "Notify people")

### **Step 7: Get Your Spreadsheet ID**

1. Open your Google Sheet
2. Look at the URL:
   ```
   https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit
                                       ^^^^^^^^^^^^^^^^^ This is your Spreadsheet ID
   ```
3. Copy this ID - you'll need it for the code

---

## 📝 Configuration File Setup

Create a file named `.env` (or update existing) with:

```bash
# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Existing Gemini Config
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🔐 Security Notes

1. **NEVER commit `service_account.json` to Git**
   - Add to `.gitignore` (already configured)
2. **Protect your Spreadsheet ID**
   - Use environment variables
3. **Limit service account permissions**
   - Only grant access to specific sheets
4. **Regularly rotate keys**
   - Delete old service accounts when not needed

---

## 📦 Python Dependencies

Add to `requirements.txt`:

```
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
```

Install:
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## ✅ Next Steps

Once you've completed the setup above, you'll receive:
1. ✅ Python script to push data to Google Sheets
2. ✅ Example code to append consultation data
3. ✅ Automated workflow integration

---

## 📊 Expected Output Format

**Sheet 1 Example Row:**
```
1 | 2025-10-16 19:19:03 | Margaret Thompson | Assisted Living | $5,500 | immediate | 14526 | Enhanced services | 5 | 31 | Community 31 | $3,528 | 3.83 | 37.0 | Great option... | 72.65 | $0.004770 | New | John Smith | Called client...
```

**Sheet 2 Example Rows (5 recommendations):**
```
1 | Margaret Thompson | 1 | 31 | Community 31 | $3,528 | 3.83 | Available | 37.0 | 4 | 6 | 2 | 1 | Great option... | 100% | Yes | | |
1 | Margaret Thompson | 2 | 36 | Community 36 | $3,169 | 13.49 | Available | 48.5 | 4 | 4 | 12 | 6 | Excellent value... | 100% | Yes | | |
...
```

---

**Ready to proceed? Let me know when you've completed Steps 1-7, and I'll provide the Python integration code!**
