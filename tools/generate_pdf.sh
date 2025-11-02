#!/bin/bash

# PDF Generation Script for DBMS Project Submission
# This script converts the Markdown document to a professional PDF

echo "🎨 FraudGuard DBMS Project - PDF Generator"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/safalgupta/Desktop/AI_FRAUD_DETECTION"
MD_FILE="$PROJECT_DIR/DBMS_PROJECT_SUBMISSION.md"
PDF_FILE="$PROJECT_DIR/DBMS_PROJECT_SUBMISSION.pdf"

# Check if markdown file exists
if [ ! -f "$MD_FILE" ]; then
    echo "❌ Error: Markdown file not found at $MD_FILE"
    exit 1
fi

echo "📄 Input file: $MD_FILE"
echo "📑 Output file: $PDF_FILE"
echo ""

# Check for pandoc
if command -v pandoc &> /dev/null; then
    echo "✅ Pandoc found!"
    echo "🔄 Converting to PDF using Pandoc..."
    
    pandoc "$MD_FILE" -o "$PDF_FILE" \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=3 \
        --variable=geometry:margin=1in \
        --variable=fontsize=11pt \
        --variable=documentclass:article \
        --highlight-style=tango \
        --metadata title="DBMS Project Submission: FraudGuard" \
        --metadata author="[Your Name]" \
        --metadata date="October 30, 2025"
    
    if [ $? -eq 0 ]; then
        echo "✅ PDF created successfully!"
        echo "📂 Location: $PDF_FILE"
        
        # Open PDF automatically
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "🔍 Opening PDF..."
            open "$PDF_FILE"
        fi
    else
        echo "❌ Pandoc conversion failed!"
        echo "💡 Trying alternative method..."
    fi
else
    echo "⚠️  Pandoc not found!"
    echo ""
    echo "📥 Install Options:"
    echo "   1. Mac: brew install pandoc"
    echo "   2. Mac: brew install --cask mactex  (for PDF support)"
    echo ""
    echo "📚 Alternative Methods:"
    echo ""
    echo "   Option A: VS Code Extension"
    echo "   --------------------------"
    echo "   1. Install 'Markdown PDF' extension"
    echo "   2. Open $MD_FILE in VS Code"
    echo "   3. Right-click → 'Markdown PDF: Export (pdf)'"
    echo ""
    echo "   Option B: Online Converter"
    echo "   -------------------------"
    echo "   1. Visit: https://www.markdowntopdf.com/"
    echo "   2. Upload: $MD_FILE"
    echo "   3. Download PDF"
    echo ""
    echo "   Option C: Google Docs"
    echo "   --------------------"
    echo "   1. Open: https://docs.google.com/"
    echo "   2. Copy content from $MD_FILE"
    echo "   3. Paste into new document"
    echo "   4. File → Download → PDF"
    echo ""
    
    # Try to open the markdown file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🔍 Opening markdown file in default editor..."
        open "$MD_FILE"
    fi
fi

echo ""
echo "📝 Next Steps:"
echo "   1. Paste screenshots in marked locations"
echo "   2. Fill in your name and roll number"
echo "   3. Update 'Before' and 'After' values in tables"
echo "   4. Review all sections"
echo "   5. Convert to final PDF"
echo ""
echo "✅ Done!"

