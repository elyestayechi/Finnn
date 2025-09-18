# analyse.py - Complete version with both command line and direct execution support
import logging
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import LOG_FILE, PDF_DIR
from src.data_loader import DataLoader
from src.risk_engine import RiskEngine, BusinessRulesEngine
from src.llm import LLMAnalyzer, LoanVectorDB
from src.reporting import ProfessionalPDF

async def configure_logging(log_file: Path = LOG_FILE) -> None:
    """Configure comprehensive logging setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler()
        ]
    )
    
    # Configure library log levels
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('fpdf').setLevel(logging.ERROR)
    logging.getLogger('fontTools').setLevel(logging.WARNING)
    logging.getLogger('fontTools.subset').setLevel(logging.ERROR)

async def log_system_info() -> None:
    """Log important system information"""
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Starting new loan assessment session")
    logger.info(f"Execution time: {datetime.now().isoformat()}")
    logger.info("="*50)

async def initialize_components() -> tuple:
    """Initialize all system components"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing system components")
        
        # Core components
        data_loader = DataLoader()
        rules = data_loader.load_rules()  
        
        risk_engine = RiskEngine(rules)
        business_rules = BusinessRulesEngine()
        vector_db = LoanVectorDB()
        
        # LLM components
        llm_analyzer = LLMAnalyzer(vector_db)
        
        logger.info("All components initialized successfully")
        return data_loader, risk_engine, business_rules, vector_db, llm_analyzer
        
    except Exception as e:
        logger.error("Component initialization failed: %s", str(e))
        raise

async def process_loan(data_loader: DataLoader, 
                     risk_engine: RiskEngine,
                     business_rules: BusinessRulesEngine,
                     llm_analyzer: LLMAnalyzer,
                     loan_id: Optional[str] = None,
                     external_id: Optional[str] = None) -> Dict[str, Any]:
    """Process a single loan application through the full pipeline"""
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate data
        logger.info("Fetching loan data from API")
        raw_loan_data = await data_loader.load_loan_data(loan_id, external_id)
        
        if not raw_loan_data:
            raise ValueError("No loan data received from API")
        
        logger.debug("Raw loan data received (not showing full content for security)")
        
        # Risk assessment
        logger.info("Performing risk assessment")
        assessment = risk_engine.evaluate(raw_loan_data)
        
        if not assessment.get('risk_assessment'):
            raise ValueError("Risk assessment failed - no results")
            
        logger.info(
            "Risk assessment completed - Score: %.1f, Level: %s",
            assessment['risk_assessment']['total_score'],
            assessment['risk_assessment']['risk_level']
        )
        
        # Business rules
        logger.info("Applying business rules")
        rule_results = business_rules.apply_rules(assessment)
        assessment['business_rules'] = rule_results
        
        # AI Analysis
        logger.info("Starting AI analysis")
        analysis = llm_analyzer.analyze_loan(assessment)
        assessment['llm_analysis'] = analysis
        
        logger.info(
            "AI Recommendation: %s",
            analysis['recommendation'].upper()
        )
        
        return assessment
        
    except Exception as e:
        logger.error("Loan processing failed: %s", str(e))
        raise
    
async def generate_report(assessment: Dict[str, Any]) -> Path:
    """Generate PDF report from assessment"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Generating PDF report")

        # Create report with timestamp
        loan_id = assessment['loan_info']['basic_info'].get('loan_id', 'unknown')
        report_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = PDF_DIR / f"loan_assessment_{loan_id}_{report_date}.pdf"
        
        pdf = ProfessionalPDF()
        pdf.generate_report(assessment, report_filename)
        
        logger.info("Report generated: %s", report_filename)
        return report_filename
        
    except Exception as e:
        logger.error("Report generation failed: %s", str(e))
        raise

async def run_loan_processing(loan_id: Optional[str] = None, 
                            external_id: Optional[str] = None) -> Path:
    """Run the complete loan processing pipeline"""
    try:
        # Setup environment
        await configure_logging()
        await log_system_info()
        logger = logging.getLogger(__name__)
        
        # Initialize system
        components = await initialize_components()
        data_loader, risk_engine, business_rules, vector_db, llm_analyzer = components
        
        # Process loan
        assessment = await process_loan(
            data_loader, risk_engine, business_rules, llm_analyzer,
            loan_id, external_id
        )
        
        # Generate outputs
        report_path = await generate_report(assessment)
        
        # Store loan in vector DB
        try:
            llm_analyzer.store_current_loan(assessment)
        except Exception as e:
            logger.warning("Failed to store loan in vector DB: %s", str(e))
        
        logger.info("="*50)
        logger.info("Processing completed successfully")
        logger.info("Final report: %s", report_path.resolve())
        logger.info("="*50)
        
        return report_path
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.critical(
            "Fatal error in loan processing:\n%s\n%s",
            str(e),
            traceback.format_exc()
        )
        raise SystemExit(1) from e
    finally:
        await data_loader.close()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run loan analysis')
    parser.add_argument('--loan-id', type=str, help='Loan ID to analyze')
    parser.add_argument('--external-id', type=str, help='External ID to analyze')
    parser.add_argument('--notes', type=str, help='Additional notes for the analysis')
    return parser.parse_args()

def main():
    """Main function for direct execution"""
    args = parse_arguments()
    
    # Use provided IDs or fall back to defaults if running directly
    loan_id = args.loan_id if args.loan_id else "33415"
    external_id = args.external_id if args.external_id else "33421"
    
    print(f"Starting analysis with Loan ID: {loan_id}, External ID: {external_id}")
    if args.notes:
        print(f"Notes: {args.notes}")
    
    # Run the analysis
    asyncio.run(run_loan_processing(loan_id=loan_id, external_id=external_id))

# Function to be called from the frontend
async def run_analysis_from_frontend(loan_id: str, external_id: str, notes: Optional[str] = None):
    """Run analysis with parameters from frontend"""
    print(f"Starting analysis from frontend with Loan ID: {loan_id}, External ID: {external_id}")
    if notes:
        print(f"Notes: {notes}")
    
    return await run_loan_processing(loan_id=loan_id, external_id=external_id)

if __name__ == "__main__":
    # This runs when executed directly from command line
    main()