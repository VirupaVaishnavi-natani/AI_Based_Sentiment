import time
import database
import analyzer

def run_validation():
    print("==================================================")
    print("   Starting SentiMind AI Programmatic Validation  ")
    print("==================================================")
    
    # 1. Check DB type
    db_status = database.get_db_status()
    print(f"Active Storage Layer: {db_status['type']}")
    print(f"Storage Host/Path: {db_status['host']}")
    
    # 2. Run Test 1 (Positive)
    print("\nRunning Test 1: Positive Review")
    text_pos = "This product is absolutely amazing! I love it and recommend it to everyone."
    res_pos = analyzer.analyze_sentiment(text_pos)
    print(f"Text: '{text_pos}'")
    print(f"Sentiment: {res_pos['sentiment']} | Confidence: {res_pos['confidence']} | Method: {res_pos['method']}")
    
    # Assert
    assert res_pos['sentiment'] == 'positive', f"Expected positive, got {res_pos['sentiment']}"
    
    # 3. Run Test 2 (Negative)
    print("\nRunning Test 2: Negative Review")
    text_neg = "This is a terrible product, extremely slow and broke on first use. Hate it."
    res_neg = analyzer.analyze_sentiment(text_neg)
    print(f"Text: '{text_neg}'")
    print(f"Sentiment: {res_neg['sentiment']} | Confidence: {res_neg['confidence']} | Method: {res_neg['method']}")
    
    # Assert
    assert res_neg['sentiment'] == 'negative', f"Expected negative, got {res_neg['sentiment']}"

    # 4. Run Test 3 (Neutral)
    print("\nRunning Test 3: Neutral Review")
    text_neu = "It is an average item. The package arrived on time, but nothing special."
    res_neu = analyzer.analyze_sentiment(text_neu)
    print(f"Text: '{text_neu}'")
    print(f"Sentiment: {res_neu['sentiment']} | Confidence: {res_neu['confidence']} | Method: {res_neu['method']}")
    
    # Assert
    assert res_neu['sentiment'] == 'neutral', f"Expected neutral, got {res_neu['sentiment']}"
    
    # 5. Check persistence
    print("\nSaving test reviews to database...")
    id_pos = database.save_review(text_pos, res_pos['sentiment'], res_pos['confidence'])
    id_neg = database.save_review(text_neg, res_neg['sentiment'], res_neg['confidence'])
    id_neu = database.save_review(text_neu, res_neu['sentiment'], res_neu['confidence'])
    
    print(f"Saved review IDs: Pos={id_pos}, Neg={id_neg}, Neu={id_neu}")
    
    # 6. Retrieve History
    print("\nRetrieving history from database...")
    history = database.get_reviews_history(limit=5)
    print(f"Total retrieved from log: {len(history)} items")
    for item in history:
        print(f"- [{item['sentiment'].upper()}] (Conf: {item['confidence'] * 100:.1f}%) {item['text'][:60]}...")
        
    # 7. Check Aggregates
    print("\nGenerating Aggregate Statistics...")
    stats = database.get_sentiment_statistics()
    print(f"Total reviews in system: {stats['total']}")
    print(f"Counts: Positive={stats['counts']['positive']}, Neutral={stats['counts']['neutral']}, Negative={stats['counts']['negative']}")
    print(f"Avg Confidences: Positive={stats['averages']['positive'] * 100:.1f}%, Neutral={stats['averages']['neutral'] * 100:.1f}%, Negative={stats['averages']['negative'] * 100:.1f}%")
    
    # Clean up test rows so database remains clean
    print("\nCleaning up test reviews...")
    d_pos = database.delete_review(id_pos)
    d_neg = database.delete_review(id_neg)
    d_neu = database.delete_review(id_neu)
    print(f"Deleted successfully: Pos={d_pos}, Neg={d_neg}, Neu={d_neu}")
    
    print("\n==================================================")
    print("      ALL PROGRAMMATIC VALIDATIONS PASSED!        ")
    print("==================================================")

if __name__ == "__main__":
    # Give the background transformer loading thread 5 seconds to load if possible, 
    # but the lexicon fallback will handle it instantly if it's not ready.
    print("Waiting 3 seconds to let Hugging Face background thread initialize...")
    time.sleep(3)
    run_validation()
