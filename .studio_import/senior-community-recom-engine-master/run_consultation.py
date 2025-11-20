"""
Run Senior Living Consultation
===============================
Process audio consultation and push to Google Sheets CRM

Usage:
    python run_consultation.py --audio "audio-files/Transcript 1 (Margaret Thompson).m4a"
    python run_consultation.py --audio "path/to/consultation.m4a"
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from main_pipeline_ranking import RankingBasedRecommendationSystem
from google_sheets_integration import push_to_crm

# Load environment variables
load_dotenv()

def main():
    """Main entry point for consultation processing"""

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process senior living consultation audio and push to Google Sheets CRM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_consultation.py --audio "audio-files/Transcript 1 (Margaret Thompson).m4a"
  python run_consultation.py --audio "consultation_2024_01_15.m4a"
        """
    )

    parser.add_argument(
        '--audio',
        type=str,
        required=True,
        help='Path to the audio file (m4a, mp3, wav, etc.)'
    )

    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Process audio but do NOT push to Google Sheets (testing only)'
    )

    args = parser.parse_args()

    # Validate audio file exists
    if not os.path.exists(args.audio):
        print(f"\n[ERROR] Audio file not found: {args.audio}")
        print("\nAvailable audio files:")
        audio_dir = Path("audio-files")
        if audio_dir.exists():
            for audio_file in sorted(audio_dir.glob("*.m4a")):
                print(f"  - {audio_file}")
        sys.exit(1)

    print("\n" + "="*80)
    print("SENIOR LIVING CONSULTATION PROCESSOR")
    print("="*80)
    print(f"\n[AUDIO FILE] {args.audio}")
    print(f"[PUSH TO CRM] {'No (testing mode)' if args.no_push else 'Yes'}")

    # Initialize system
    print("\n[STEP 1/3] Initializing recommendation system...")
    system = RankingBasedRecommendationSystem()

    # Process audio file
    print(f"\n[STEP 2/3] Processing consultation...")
    try:
        result = system.process_audio_file(args.audio)

        # Display summary
        client_name = result.get('client_info', {}).get('name', 'Unknown')
        num_recommendations = len(result.get('recommendations', []))
        processing_time = result.get('metrics', {}).get('total_time', 0)
        total_cost = result.get('metrics', {}).get('costs', {}).get('total_cost', 0)

        print(f"\n[SUCCESS] Processing complete!")
        print(f"  - Client: {client_name}")
        print(f"  - Recommendations: {num_recommendations}")
        print(f"  - Processing time: {processing_time:.1f}s")
        print(f"  - Total cost: ${total_cost:.6f}")

    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Push to Google Sheets (unless --no-push flag)
    if not args.no_push:
        print(f"\n[STEP 3/3] Pushing to Google Sheets CRM...")

        try:
            crm_result = push_to_crm(result)

            consultation_id = crm_result['consultation_id']

            print(f"\n[SUCCESS] Consultation #{consultation_id} added to CRM!")
            print(f"  - Client Consultations: Row {crm_result['rows_added']['consultation']}")
            print(f"  - Recommendations Detail: {len(crm_result['rows_added']['recommendations'])} rows added")
            print(f"  - Performance Analytics: Row {crm_result['rows_added']['performance']}")

            # Get spreadsheet URL
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

            print(f"\n[VIEW CRM] {sheet_url}")

        except Exception as e:
            print(f"\n[ERROR] Failed to push to Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"\n[STEP 3/3] Skipped (--no-push flag enabled)")

    print("\n" + "="*80)
    print("CONSULTATION COMPLETE!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
