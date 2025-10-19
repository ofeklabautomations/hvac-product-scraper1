# HVAC Product Importer Web Scraper

A Python + Playwright web scraper for HVAC manufacturer websites that extracts product specifications, downloads PDFs, and outputs normalized CSV data.

## Features

- **Web Scraping**: Visits product pages, collects product links, finds and downloads PDFs
- **Data Extraction**: Grabs spec tables from HTML and PDFs using BeautifulSoup and pdfplumber
- **Normalization**: Maps raw specs to canonical fields with unit conversion using pint
- **Product Classification**: Automatically classifies products (RTU, chiller, AHU, etc.)
- **Respectful Crawling**: Honors robots.txt, configurable delays, proper user agents
- **Flexible Input**: Support both seed-file mode and one-URL mode

## Quick Start (Mac)

### 1. Setup

```bash
# Clone or download the project
cd load55-productimporter

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m playwright install
```

### 2. Run Examples

**One-URL mode** (paste any HVAC manufacturer URL):
```bash
python -m src.crawl --url "https://www.aaon.com/products/" --manufacturer "AAON" --limit 50
```

**Seed mode** (using configuration file):
```bash
python -m src.crawl --seed ./seeds/aaon.json --limit 50
```

**With product type override**:
```bash
python -m src.crawl --url "https://example.com/products/" --manufacturer "EXAMPLE" --default_product_type rtu --limit 100
```

## Output Files

- `output/products.csv` - Raw product data with specs as JSON
- `output/documents.csv` - Downloaded PDF metadata with SHA256 hashes  
- `output/normalized_products.csv` - Clean normalized data ready for database import
- `output/files/` - Downloaded PDFs with hash-based filenames

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Edit `.env`:
```env
USER_AGENT=Load55Scraper/0.2 (+https://yourcompany.com)
OUTPUT_DIR=output
CRAWL_DELAY=2
```

### Seed Files

Create manufacturer-specific seed files in `seeds/` directory:

```json
{
  "manufacturer": "MANUFACTURER_NAME",
  "base_url": "https://www.manufacturer.com",
  "start_urls": ["https://www.manufacturer.com/products/"],
  "product_link_selectors": [
    "a[href*='/product']",
    "a[href*='/products/']"
  ],
  "deny_patterns": ["news", "blog", "careers"],
  "pdf_keywords": ["submittal", "spec", "catalog", "manual"],
  "max_depth": 2
}
```

### Spec Catalog

Edit `specs/spec_catalog.json` to define canonical fields and units for each product type. The system will automatically map raw scraped data to these canonical fields.

## Adding New Manufacturers

1. **Create seed file**: Duplicate `seeds/aaon.json` and update with manufacturer details
2. **Test selectors**: Run with small limit to verify product links are found
3. **Tune selectors**: Adjust `product_link_selectors` if needed
4. **Scale up**: Increase `--limit` for full crawl

## Technical Details

### Dependencies

- **playwright**: Browser automation for JavaScript-heavy sites
- **beautifulsoup4**: HTML parsing and extraction
- **pdfplumber**: PDF table extraction
- **pint**: Unit conversion (tons↔kW, in↔cm, lb↔kg)
- **pydantic**: Configuration validation
- **tenacity**: Retry logic for network requests

### Architecture

- **Modular design**: Separate modules for parsing, normalization, saving
- **Package structure**: Run as `python -m src.crawl` for clean imports
- **Respectful crawling**: robots.txt compliance, configurable delays
- **Error handling**: Graceful failure with retry logic

## Troubleshooting

### Common Issues

1. **No products found**: Check `product_link_selectors` in seed file
2. **Import errors**: Ensure you're running from project root with `python -m src.crawl`
3. **PDF download fails**: Check if site requires authentication or has anti-bot measures
4. **Normalization issues**: Verify `specs/spec_catalog.json` has correct field mappings

### Debugging

Enable verbose output by modifying the crawler or adding print statements in the parsing modules.

## Legal & Ethical

- **Always respect robots.txt**: The scraper checks robots.txt before crawling
- **Be polite**: Use reasonable delays between requests (default 2 seconds)
- **Check Terms of Use**: Some sites may prohibit scraping
- **Rate limiting**: Don't overwhelm servers with too many concurrent requests

## Next Steps

- **Database integration**: Import normalized CSV into your database
- **Spec mapping**: Expand `spec_catalog.json` with your complete field schema
- **Product validation**: Add AHRI lookup for model validation
- **Advanced parsing**: Upgrade to Camelot for better PDF table extraction

## Support

For issues or questions, check the code comments in each module or refer to the individual file documentation.
