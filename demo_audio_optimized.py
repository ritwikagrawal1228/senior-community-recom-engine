"""
Demo: Test optimized database with audio file
"""
from main_pipeline_ranking import RankingBasedRecommendationSystem

def demo_with_audio():
    print("="*80)
    print("DEMO: OPTIMIZED DATABASE + AUDIO PROCESSING")
    print("="*80)

    # Initialize system with optimized database (default)
    print("\n[STEP 1] Initializing system with optimized database...")
    system = RankingBasedRecommendationSystem()

    # Process audio file
    print("\n[STEP 2] Processing audio file: 'Calling Transcript.m4a'")
    result = system.process_audio_file(
        audio_path='Calling Transcript.m4a',
        output_file='audio_demo_output_optimized.json'
    )

    # Print detailed results
    print("\n" + "="*80)
    print("DEMO RESULTS")
    print("="*80)

    if result['recommendations']:
        print(f"\nTotal recommendations: {result['summary']['total_matches']}")
        print(f"\n[TOP 5 RECOMMENDATIONS]:")

        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"\n#{i}. Community {rec['community_id']}")
            print(f"    Combined Rank Score: {rec['combined_rank_score']:.2f} (lower is better)")
            print(f"    Monthly Fee: ${rec['key_metrics']['monthly_fee']:,.0f}")
            print(f"    Distance: {rec['key_metrics']['distance_miles']:.2f} miles")
            print(f"    Availability: {rec['key_metrics']['est_waitlist']}")
            print(f"    Business Rank: #{rec['rankings']['business_rank']}")
            print(f"    Holistic Reason: {rec['explanations']['holistic_reason'][:100]}...")
    else:
        print("\n[WARNING] No recommendations found!")
        print(f"Message: {result['summary'].get('message', 'Unknown')}")

    print("\n" + "="*80)
    print("[SUCCESS] Demo complete!")
    print(f"[INFO] Full results saved to: audio_demo_output_optimized.json")
    print("="*80)

    return result


if __name__ == '__main__':
    result = demo_with_audio()
