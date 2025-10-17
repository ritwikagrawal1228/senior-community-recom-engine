"""
Demo: Test optimized database with text input
"""
from main_pipeline_ranking import RankingBasedRecommendationSystem

def demo_with_text():
    print("="*80)
    print("DEMO: OPTIMIZED DATABASE + TEXT PROCESSING")
    print("="*80)

    # Sample conversation from audio transcript
    sample_conversation = """
    Consultant: Hello, I'm calling to help you find a senior living community.
    Can you tell me what type of care you're looking for?

    Client: Hi, yes. My mother needs memory care. She has Alzheimer's and needs
    specialized support. She's 78 years old.

    Consultant: I understand. What's your budget for monthly costs?

    Client: We can afford around $7,000 per month, maybe a bit more if needed.

    Consultant: And when are you looking to move her in?

    Client: Within the next 2-3 months. We want to find the right place first.

    Consultant: Do you have a preferred location or area?

    Client: We live in Brighton, so somewhere close to ZIP 14618 would be ideal.
    She prefers a private room if possible.

    Consultant: Perfect, that helps a lot. Let me find some good options for you.
    """

    # Initialize system with optimized database (default)
    print("\n[STEP 1] Initializing system with optimized database...")
    system = RankingBasedRecommendationSystem()

    # Process text conversation
    print("\n[STEP 2] Processing conversation...")
    result = system.process_text_input(
        text=sample_conversation,
        output_file='text_demo_output_optimized.json'
    )

    # Print detailed results
    print("\n" + "="*80)
    print("DEMO RESULTS")
    print("="*80)

    if result['recommendations']:
        print(f"\n[CLIENT INFO]")
        print(f"  Care Level: {result['client_info']['care_level']}")
        print(f"  Budget: ${result['client_info']['budget']:,.0f}/month")
        print(f"  Timeline: {result['client_info']['timeline']}")
        print(f"  Location: {result['client_info']['location_preference']}")

        print(f"\n[RANKING SUMMARY]")
        print(f"  Total communities ranked: {result['summary']['total_matches']}")
        print(f"  Average monthly fee: ${result['summary']['avg_monthly_fee']:,.0f}")
        print(f"  Average distance: {result['summary']['avg_distance_miles']:.2f} miles")

        print(f"\n[TOP 5 RECOMMENDATIONS]:")

        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"\n  #{i}. Community {rec['community_id']}")
            print(f"      Combined Rank Score: {rec['combined_rank_score']:.2f} (lower is better)")
            print(f"      Monthly Fee: ${rec['key_metrics']['monthly_fee']:,.0f}")
            print(f"      Distance: {rec['key_metrics']['distance_miles']:.2f} miles")
            print(f"      Availability: {rec['key_metrics']['est_waitlist']}")

            # Show individual dimension ranks
            print(f"      Individual Ranks:")
            for dim, rank in rec['rankings'].items():
                print(f"        - {dim}: #{rank}")

            print(f"      Holistic Reason: {rec['explanations']['holistic_reason'][:150]}...")
    else:
        print("\n[WARNING] No recommendations found!")
        print(f"Message: {result['summary'].get('message', 'Unknown')}")

    print("\n" + "="*80)
    print("[SUCCESS] Demo complete!")
    print(f"[INFO] Full results saved to: text_demo_output_optimized.json")
    print("="*80)

    return result


if __name__ == '__main__':
    result = demo_with_text()
