import argparse
from rag import RAGPipeline

def main():
    parser = argparse.ArgumentParser(description='GenAI Document Assistant')
    parser.add_argument('--file', type=str, help='Path to document file')
    parser.add_argument('--query', type=str, help='Question to ask')
    
    args = parser.parse_args()
    
    rag = RAGPipeline()
    
    if args.file:
        rag.add_document(args.file)
    
    if args.query:
        print("\n" + "="*50)
        print("ANSWER")
        print("="*50)
        answer = rag.query(args.query)
        print(answer)
        print("="*50 + "\n")

if __name__ == '__main__':
    main()
    
