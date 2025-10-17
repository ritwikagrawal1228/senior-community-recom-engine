"""
Simple Demo: Test optimized database without apartment type filter
"""
from main_pipeline_ranking import RankingBasedRecommendationSystem

def demo_simple():
    print("="*80)
    print("SIMPLE DEMO: OPTIMIZED DATABASE")
    print("="*80)

    # Simple conversation without apartment type specification
    sample_conversation = """
    Client: My mother needs memory care. She has Alzheimer's.
    Budget is around $7,000 per month.
    Timeline is within 2-3 months.
    Location: Brighton area, ZIP 14618.
    """

    print("\n[STEP 1] Initializing with optimized database...")
    system = RankingBasedRecommendationSystem()

    print("\n[STEP 2] Processing conversation...")
    result = system.process_text_input(
        text=sample_conversation,
        output_file='simple_demo_output.json'
    )

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if result['recommendations']:
        print(f"\n[SUCCESS] Found {result['summary']['total_matches']} communities!")

        print(f"\n[TOP 3 RECOMMENDATIONS]:")
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"\n#{i}. Community {rec['community_id']}")
            print(f"    Combined Rank Score: {rec['combined_rank_score']:.2f} (lower is better)")
            print(f"    Monthly Fee: ${rec['key_metrics']['monthly_fee']:,.0f}")
            print(f"    Distance: {rec['key_metrics']['distance_miles']:.2f} miles")
            print(f"    Availability: {rec['key_metrics']['est_waitlist']}")
            print(f"    Ranks: Business=#{rec['rankings']['business_rank']}, " +
                  f"Distance=#{rec['rankings']['distance_rank']}, " +
                  f"Availability=#{rec['rankings']['availability_rank']}")
            print(f"    Why: {rec['explanations']['holistic_reason'][:120]}...")
    else:
        print(f"\n[NO MATCHES] {result['summary'].get('message', 'No communities found')}")

    print("\n" + "="*80)
    print(f"[SAVED] Full results: simple_demo_output.json")
    print("="*80)

    return result


if __name__ == '__main__':
    result = demo_simple()
