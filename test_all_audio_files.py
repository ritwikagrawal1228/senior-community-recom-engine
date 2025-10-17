"""
Test all 5 audio files with E2E timing and token counting
Includes 2-minute breaks between tests to avoid API overload
"""

import os
import json
import time
from main_pipeline_ranking import RankingBasedRecommendationSystem

def test_all_audio_files():
    """Test all audio files and collect performance metrics"""

    # Audio files to test
    audio_files = [
        ("audio-files/Transcript 1 (Margaret Thompson).m4a", "Margaret Thompson"),
        ("audio-files/Transcript 2 (Bob Martinez).m4a", "Bob Martinez"),
        ("audio-files/Transcript 3 (Dorothy Chen).m4a", "Dorothy Chen"),
        ("audio-files/Transcript 4 (Frank and Betty Williams).m4a", "Frank and Betty Williams"),
        ("audio-files/Transcript 5 (Alice Rodriguez).m4a", "Alice Rodriguez")
    ]

    # Initialize system
    print("\n" + "="*80)
    print("TESTING ALL AUDIO FILES WITH E2E TIMING")
    print("="*80)

    system = RankingBasedRecommendationSystem(
        data_file_path="DataFile_students_OPTIMIZED.xlsx"
    )

    # Store results for comparison
    all_results = []

    # Test each audio file
    for i, (audio_path, client_name) in enumerate(audio_files, 1):
        print("\n" + "="*80)
        print(f"TEST {i}/5: {client_name}")
        print("="*80)

        if not os.path.exists(audio_path):
            print(f"[ERROR] Audio file not found: {audio_path}")
            continue

        try:
            # Process audio file
            output_file = f"output/audio_test_{i}_{client_name.replace(' ', '_')}.json"
            result = system.process_audio_file(audio_path, output_file=output_file)

            # Extract metrics
            metrics = result.get('performance_metrics', {})
            timings = metrics.get('timings', {})
            tokens = metrics.get('token_counts', {})

            # Store summary
            summary = {
                'test_number': i,
                'client_name': client_name,
                'audio_file': audio_path,
                'total_time': timings.get('e2e_total', 0),
                'extraction_time': timings.get('phase1_extraction', 0),
                'filtering_time': timings.get('phase2_filtering', 0),
                'ranking_time': timings.get('phase3_ranking', 0),
                'output_time': timings.get('phase4_output', 0),
                'total_tokens': tokens.get('total_tokens', 0),
                'input_tokens': tokens.get('total_input_tokens', 0),
                'output_tokens': tokens.get('total_output_tokens', 0),
                'api_calls': metrics.get('api_calls', 0),
                'throughput': tokens.get('total_tokens', 0) / timings.get('e2e_total', 1),
                'total_recommendations': result.get('summary', {}).get('total_matches', 0),
                'top_community': result['recommendations'][0]['community_id'] if result.get('recommendations') else None,
                'top_score': result['recommendations'][0]['combined_rank_score'] if result.get('recommendations') else None
            }
            all_results.append(summary)

            print(f"\n[SUCCESS] Test {i} completed!")
            print(f"  - Recommendations: {summary['total_recommendations']}")
            print(f"  - E2E Time: {summary['total_time']:.2f}s")
            print(f"  - Total Tokens: ~{summary['total_tokens']:,}")
            print(f"  - Output saved: {output_file}")

        except Exception as e:
            print(f"\n[ERROR] Test {i} failed: {str(e)}")
            import traceback
            traceback.print_exc()

        # Add 2-minute break between tests to avoid API overload (except after last test)
        if i < len(audio_files):
            print(f"\n{'='*80}")
            print(f"[WAITING] 2-minute break before next test to avoid API overload...")
            print(f"{'='*80}")
            for remaining in range(120, 0, -10):
                print(f"  Time remaining: {remaining} seconds...", end='\r')
                time.sleep(10)
            print("\n")

    # Print comparison summary
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON ACROSS ALL TESTS")
    print("="*80)

    if all_results:
        print(f"\n{'Test':<6} {'Client Name':<30} {'E2E Time':<12} {'Tokens':<10} {'Throughput':<12} {'Recs':<6}")
        print("-" * 80)

        for r in all_results:
            print(f"{r['test_number']:<6} {r['client_name']:<30} {r['total_time']:>8.2f}s    {r['total_tokens']:>8,}  {r['throughput']:>8.0f} t/s  {r['total_recommendations']:>4}")

        # Calculate averages
        avg_time = sum(r['total_time'] for r in all_results) / len(all_results)
        avg_tokens = sum(r['total_tokens'] for r in all_results) / len(all_results)
        avg_throughput = sum(r['throughput'] for r in all_results) / len(all_results)

        print("-" * 80)
        print(f"{'AVG':<6} {'':<30} {avg_time:>8.2f}s    {avg_tokens:>8,.0f}  {avg_throughput:>8.0f} t/s")

        # Phase breakdown
        print("\n" + "="*80)
        print("PHASE TIMING BREAKDOWN (Average)")
        print("="*80)

        avg_extraction = sum(r['extraction_time'] for r in all_results) / len(all_results)
        avg_filtering = sum(r['filtering_time'] for r in all_results) / len(all_results)
        avg_ranking = sum(r['ranking_time'] for r in all_results) / len(all_results)
        avg_output = sum(r['output_time'] for r in all_results) / len(all_results)

        print(f"  Phase 1 (Extraction): {avg_extraction:>8.2f}s ({avg_extraction/avg_time*100:>5.1f}%)")
        print(f"  Phase 2 (Filtering):  {avg_filtering:>8.2f}s ({avg_filtering/avg_time*100:>5.1f}%)")
        print(f"  Phase 3 (Ranking):    {avg_ranking:>8.2f}s ({avg_ranking/avg_time*100:>5.1f}%)")
        print(f"  Phase 4 (Output):     {avg_output:>8.2f}s ({avg_output/avg_time*100:>5.1f}%)")

        # Save comparison report
        comparison_file = "output/all_audio_tests_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump({
                'individual_results': all_results,
                'averages': {
                    'total_time': avg_time,
                    'extraction_time': avg_extraction,
                    'filtering_time': avg_filtering,
                    'ranking_time': avg_ranking,
                    'output_time': avg_output,
                    'total_tokens': avg_tokens,
                    'throughput': avg_throughput
                }
            }, f, indent=2)

        print("\n" + "="*80)
        print(f"[SAVED] Comparison report: {comparison_file}")
        print("="*80)

    else:
        print("\n[WARNING] No results to compare")

    return all_results

if __name__ == "__main__":
    test_all_audio_files()
