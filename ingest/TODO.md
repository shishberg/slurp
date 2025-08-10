# PDF Text Extraction for RAG - TODO List

## Phase 1: Quick Baseline Comparisons

### Set up basic extraction methods
- [x] Get `unstructured` hello world working with your sample PDFs
- [ ] Set up Amazon Textract with `amazon-textract-textractor` and test `document.to_markdown()` 
- [ ] Add `pdfplumber` as a mid-range option
- [ ] Keep your current `pdftotext` baseline for comparison

### Quick quality assessment
- [ ] Extract same newsletter with all 4 methods (unstructured, Textract, pdfplumber, pdftotext)
- [ ] Manually inspect outputs for calendar/event tables
- [ ] Check if date-event relationships are preserved
- [ ] Note which method handles your specific table formats best

## Phase 2: Build Evaluation Pipeline

### Collect diverse test cases
- [ ] Gather 5-10 newsletter PDFs with different layouts
- [ ] Include examples with:
  - [ ] Calendar tables (your main use case)
  - [ ] Contact/staff lists  
  - [ ] Event announcements
  - [ ] Mixed structured/unstructured content

### Create focused eval tests
- [ ] Implement the embedding similarity test for date-event pairs
- [ ] Create test queries like "When is athletics carnival?" 
- [ ] Build the structural integrity test (do related concepts stay together?)
- [ ] Set up A/B comparison against current method

## Phase 3: Iterate on Best Performer

### If Textract wins:
- [ ] Test layout-aware chunking (section headers + tables)
- [ ] Experiment with different chunking strategies:
  - [ ] One row per chunk with headers
  - [ ] Grouped calendar entries
  - [ ] Contextual chunks with surrounding text
- [ ] Measure cost implications vs quality gains

### If unstructured wins:
- [ ] Try different chunking strategies (`chunk_by_title`, `chunk_by_page`, etc.)
- [ ] Experiment with chunk size parameters
- [ ] Test if it handles your calendar tables well

### If simple approaches aren't enough:
- [ ] Implement selective LLM cleanup for problematic sections
- [ ] Create hybrid pipeline (simple extraction + LLM enhancement for flagged cases)
- [ ] Build confidence scoring to decide when to use expensive processing

## Phase 4: Production Considerations

### Integration
- [ ] Integrate best method with AWS Bedrock Knowledge Base
- [ ] Test chunking with your embedding model
- [ ] Benchmark end-to-end RAG performance

### Monitoring & Quality
- [ ] Set up logging for extraction quality issues
- [ ] Create process for flagging documents that need manual review
- [ ] Plan for handling edge cases in production

### Cost optimization
- [ ] Measure actual costs for chosen approach
- [ ] Implement batching if using Textract
- [ ] Consider caching for repeated processing

## Immediate Next Steps (Start Here)

1. **Get the hello world working** - `unstructured` + `textractor` basic examples
2. **Extract one sample PDF** with both methods + your current baseline  
3. **Manual inspection** - which preserves your calendar table structure best?
4. **Pick the most promising** method and build eval pipeline around it

## Questions to Answer Through Testing

- Does `document.to_markdown()` naturally preserve enough context?
- How much does layout-aware processing actually help for your use case?
- What's the sweet spot between extraction quality and cost/complexity?
- Which chunking strategy works best for calendar/event queries?