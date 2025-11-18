import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid
import json
import os

# Configuration - Read from Streamlit secrets or environment variables
try:
    # Try Streamlit secrets first (for Streamlit Community Cloud)
    BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8080")
    API_KEY = st.secrets.get("API_KEY", "")
    FIREBASE_CONFIG = {
        "apiKey": st.secrets.get("FIREBASE_API_KEY", ""),
        "authDomain": st.secrets.get("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": st.secrets.get("FIREBASE_PROJECT_ID", ""),
    }
except:
    # Fallback to environment variables (for local development)
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
    API_KEY = os.getenv("API_KEY", "")
    FIREBASE_CONFIG = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    }

st.set_page_config(
    page_title="Smart Month-End Close",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Helper function to make authenticated requests
def make_request(method, endpoint, **kwargs):
    """Make authenticated API request"""
    headers = kwargs.pop('headers', {})
    
    # Add API key authentication (backend expects X-API-Key header)
    if API_KEY:
        headers['X-API-Key'] = API_KEY
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, headers=headers, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None

# Authentication functions
def sign_in_with_email_password(email, password):
    """Sign in with email/password (development mode)"""
    # Test connection to backend
    response = make_request("GET", "/health")
    if response and response.status_code == 200:
        st.session_state.authenticated = True
        st.session_state.user_email = email
        st.session_state.user_id = email.split('@')[0]
        return True
    return False

def sign_up_with_email_password(email, password):
    """Sign up with Firebase (simulated)"""
    # For development: just validate and use API key
    if email and password and len(password) >= 6:
        return sign_in_with_email_password(email, password)
    return False

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.auth_token = None
    st.session_state.user_email = None
    st.session_state.user_id = None
    st.session_state.uploaded_files = []
    st.session_state.chat_history = []
    st.rerun()

# Authentication UI
if not st.session_state.authenticated:
    st.title("📊 Smart Month-End Enclosure Generator")
    st.markdown("### Welcome! Please sign in to continue")
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        st.subheader("Sign In")
        email = st.text_input("Email", key="signin_email")
        password = st.text_input("Password", type="password", key="signin_password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Sign In", type="primary", use_container_width=True):
                if email and password:
                    with st.spinner("Signing in..."):
                        if sign_in_with_email_password(email, password):
                            st.success("✅ Signed in successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                else:
                    st.warning("Please enter email and password")
        
        st.markdown("---")
        st.info("💡 **Development Mode**: Use any email/password to sign in")
    
    with tab2:
        st.subheader("Create Account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Sign Up", type="primary", use_container_width=True):
                if new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            if sign_up_with_email_password(new_email, new_password):
                                st.success("✅ Account created! Signing in...")
                                st.rerun()
                            else:
                                st.error("❌ Failed to create account")
                else:
                    st.warning("Please fill in all fields")
    
    st.stop()

# Main App (Authenticated Users Only)
st.title("📊 Smart Month-End Enclosure Generator")
st.markdown("*Automate Financial Reporting with AI*")

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_email}")
    st.markdown(f"*User ID: {st.session_state.user_id}*")
    
    if st.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.markdown("---")
    st.header("Navigation")
    page = st.radio("Go to", ["📤 Upload", "✅ Checklist", "📊 Report", "💬 Chat"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    # Get user info
    response = make_request("GET", "/me")
    if response and response.status_code == 200:
        user_info = response.json()
        st.success("✅ Connected")
    else:
        st.warning("⚠️ Connection issue")

# Upload Page
if page == "📤 Upload":
    st.header("📤 Upload Financial Documents")
    st.markdown("Upload CSV files for month-end close processing")
    
    # Multiple file upload
    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=['csv'],
        accept_multiple_files=True,
        help="Upload bank statements, invoices, ledgers, etc."
    )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        process_single = st.button("📄 Process Files", type="primary", disabled=not uploaded_files, use_container_width=True)
    with col2:
        process_and_report = st.button("📊 Process & Generate Report", disabled=not uploaded_files, use_container_width=True)
    
    if uploaded_files and (process_single or process_and_report):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if process_and_report:
            # Use upload-multiple endpoint
            with st.spinner("Processing files and generating report..."):
                try:
                    files = [("files", (f.name, f.getvalue(), "text/csv")) for f in uploaded_files]
                    
                    response = make_request("POST", "/upload-multiple", files=files)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        
                        st.success(f"✅ Processed {result['files_processed']} files successfully!")
                        
                        # Show results
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Files Processed", result['files_processed'])
                        with col2:
                            st.metric("Files Failed", result['files_failed'])
                        with col3:
                            st.metric("Total Rows", sum(r.get('rows_processed', 0) for r in result['results']))
                        
                        # Show individual file results
                        st.subheader("📋 File Processing Results")
                        for file_result in result['results']:
                            with st.expander(f"✅ {file_result['filename']} - {file_result['doc_type']}"):
                                st.json(file_result)
                        
                        # Show errors if any
                        if result['errors']:
                            st.subheader("⚠️ Errors")
                            for error in result['errors']:
                                st.error(f"{error['filename']}: {error['error']}")
                        
                        # Show report
                        if 'report' in result:
                            st.markdown("---")
                            st.subheader("📊 Month-End Report")
                            report = result['report']
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Documents", report.get('total_documents', 0))
                            with col2:
                                st.metric("Total Rows", report.get('total_rows', 0))
                            with col3:
                                st.metric("Completion", report.get('completion_percentage', '0%'))
                            with col4:
                                st.metric("Status", report.get('status', 'N/A'))
                            
                            # Detailed report
                            with st.expander("📄 View Full Report"):
                                st.json(report)
                    else:
                        st.error(f"❌ Upload failed: {response.status_code if response else 'No response'}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            # Process files individually
            results = []
            for idx, file in enumerate(uploaded_files):
                progress_bar.progress((idx + 1) / len(uploaded_files))
                status_text.text(f"Processing {file.name}...")
                
                try:
                    files = {"file": (file.name, file.getvalue(), "text/csv")}
                    response = make_request("POST", "/upload", files=files)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        results.append({
                            "filename": file.name,
                            "status": "success",
                            "result": result
                        })
                    else:
                        results.append({
                            "filename": file.name,
                            "status": "error",
                            "error": f"Status {response.status_code if response else 'No response'}"
                        })
                except Exception as e:
                    results.append({
                        "filename": file.name,
                        "status": "error",
                        "error": str(e)
                    })
            
            progress_bar.progress(1.0)
            status_text.text("✅ Processing complete!")
            
            # Show results
            success_count = sum(1 for r in results if r['status'] == 'success')
            st.success(f"✅ Successfully processed {success_count}/{len(results)} files")
            
            for result in results:
                if result['status'] == 'success':
                    with st.expander(f"✅ {result['filename']}"):
                        data = result['result']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Document Type", data.get('classification', {}).get('doc_type', 'N/A'))
                            st.metric("Rows", data.get('extraction', {}).get('row_count', 0))
                        with col2:
                            st.metric("Confidence", f"{data.get('classification', {}).get('confidence', 0):.1%}")
                        st.json(data)
                else:
                    with st.expander(f"❌ {result['filename']}"):
                        st.error(result['error'])
    
    # Show upload tips
    st.markdown("---")
    st.markdown("### 💡 Upload Tips")
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **Supported Document Types:**
        - Bank Statements
        - Invoice Registers
        - General Ledgers
        - Trial Balances
        - Reconciliation Reports
        """)
    with col2:
        st.info("""
        **Best Practices:**
        - Upload multiple files at once
        - Use descriptive filenames
        - Ensure CSV format is valid
        - Check data quality before upload
        """)

# Checklist Page
elif page == "✅ Checklist":
    st.header("✅ Month-End Close Checklist")
    st.markdown("Track your document upload progress")
    
    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    try:
        response = make_request("GET", "/checklist")
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Extract checklist data
            if 'checklist' in data:
                checklist = data['checklist']
                required_docs = data.get('required_docs', {})
                
                # Calculate progress
                completed = len([s for s in checklist.values() if s == "uploaded"])
                total = len(required_docs)
                progress = completed / total if total > 0 else 0
                
                # Progress section
                st.markdown("### 📊 Overall Progress")
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.progress(progress)
                with col2:
                    st.metric("Completed", f"{completed}/{total}")
                with col3:
                    st.metric("Progress", f"{progress*100:.0f}%")
                
                # Status indicator
                if progress == 1.0:
                    st.success("🎉 All required documents uploaded!")
                elif progress >= 0.5:
                    st.info("📝 More than halfway there!")
                else:
                    st.warning("⚠️ Please upload required documents")
                
                st.markdown("---")
                
                # Checklist items
                st.markdown("### 📋 Document Checklist")
                
                # Separate required and optional
                required_items = {k: v for k, v in required_docs.items() if v.get('required', True)}
                optional_items = {k: v for k, v in required_docs.items() if not v.get('required', True)}
                
                # Required documents
                if required_items:
                    st.markdown("#### Required Documents")
                    for doc_type, info in required_items.items():
                        status = checklist.get(doc_type, "missing")
                        
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            if status == "uploaded":
                                st.markdown(f"✅ **{info['name']}**")
                            else:
                                st.markdown(f"❌ **{info['name']}**")
                        with col2:
                            if status == "uploaded":
                                st.success("UPLOADED")
                            else:
                                st.error("MISSING")
                        with col3:
                            if status == "missing":
                                st.button("📤", key=f"upload_{doc_type}", help="Go to Upload page")
                
                # Optional documents
                if optional_items:
                    st.markdown("#### Optional Documents")
                    for doc_type, info in optional_items.items():
                        status = checklist.get(doc_type, "missing")
                        
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            if status == "uploaded":
                                st.markdown(f"✅ {info['name']} *(optional)*")
                            else:
                                st.markdown(f"⚪ {info['name']} *(optional)*")
                        with col2:
                            if status == "uploaded":
                                st.success("UPLOADED")
                            else:
                                st.info("OPTIONAL")
                        with col3:
                            if status == "missing":
                                st.button("📤", key=f"upload_opt_{doc_type}", help="Go to Upload page")
            else:
                st.info("📝 No checklist data available. Upload documents to get started!")
        else:
            st.error(f"❌ Could not fetch checklist: {response.status_code if response else 'No response'}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Report Page
elif page == "📊 Report":
    st.header("📊 Month-End Close Report")
    st.markdown("Generate comprehensive financial close reports")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📄 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                try:
                    response = make_request("POST", "/generate-report")
                    
                    if response and response.status_code == 200:
                        report = response.json()
                        st.session_state.current_report = report
                        st.success("✅ Report generated successfully!")
                    else:
                        st.error(f"❌ Failed to generate report: {response.status_code if response else 'No response'}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display report if available
    if 'current_report' in st.session_state:
        report = st.session_state.current_report
        
        st.markdown("---")
        
        # Summary metrics
        st.markdown("### 📈 Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", report.get('total_documents', 0))
        with col2:
            st.metric("Total Rows", report.get('total_rows', 0))
        with col3:
            st.metric("Completion", report.get('completion_percentage', '0%'))
        with col4:
            status = report.get('status', 'N/A')
            if status == "Complete":
                st.success(f"✅ {status}")
            elif status == "Incomplete":
                st.warning(f"⚠️ {status}")
            else:
                st.info(f"ℹ️ {status}")
        
        # Document breakdown
        if 'documents_by_type' in report:
            st.markdown("### 📋 Documents by Type")
            docs_df = pd.DataFrame([
                {"Document Type": k, "Count": v}
                for k, v in report['documents_by_type'].items()
            ])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(docs_df, use_container_width=True, hide_index=True)
            with col2:
                if len(docs_df) > 0:
                    fig = px.pie(docs_df, values='Count', names='Document Type', 
                                title='Document Distribution')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Checklist status
        if 'checklist_status' in report:
            st.markdown("### ✅ Checklist Status")
            checklist = report['checklist_status']
            
            status_df = pd.DataFrame([
                {"Document": k, "Status": v}
                for k, v in checklist.items()
            ])
            st.dataframe(status_df, use_container_width=True, hide_index=True)
        
        # Financial summary
        if 'financial_summary' in report:
            st.markdown("### 💰 Financial Summary")
            summary = report['financial_summary']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Amount", f"${summary.get('total_amount', 0):,.2f}")
            with col2:
                st.metric("Average Transaction", f"${summary.get('avg_amount', 0):,.2f}")
            with col3:
                st.metric("Transaction Count", summary.get('transaction_count', 0))
        
        # Recommendations
        if 'recommendations' in report and report['recommendations']:
            st.markdown("### 💡 Recommendations")
            for rec in report['recommendations']:
                st.info(f"• {rec}")
        
        # Full report JSON
        with st.expander("📄 View Full Report (JSON)"):
            st.json(report)
        
        # Download report
        col1, col2 = st.columns([1, 4])
        with col1:
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label="⬇️ Download Report",
                data=report_json,
                file_name=f"month_end_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("📝 Click 'Generate Report' to create a month-end close report")
        
        # Show what's included
        st.markdown("### 📋 Report Includes:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - Document summary
            - Checklist completion status
            - Financial totals and averages
            - Document type breakdown
            """)
        with col2:
            st.markdown("""
            - Missing documents
            - Recommendations
            - Data quality metrics
            - Timestamp and metadata
            """)

# Chat Page
elif page == "💬 Chat":
    st.header("💬 AI Assistant")
    st.markdown("Ask questions about your uploaded financial data using RAG-powered search")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            with st.chat_message("user"):
                st.write(msg['content'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['content'])
                if 'search_results' in msg and msg['search_results']:
                    with st.expander("📚 Sources"):
                        for idx, result in enumerate(msg['search_results'][:3], 1):
                            st.markdown(f"**Source {idx}** (Score: {result.get('score', 0):.3f})")
                            st.text(result.get('chunk_text', '')[:200] + "...")
                            st.markdown(f"*Document: {result.get('document_id', 'N/A')}*")
                            st.markdown("---")
    
    # Chat input
    user_message = st.chat_input("Ask me anything about your financial data...")
    
    if user_message:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_message)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = make_request(
                        "POST",
                        "/chat",
                        params={
                            "message": user_message,
                            "session_id": st.session_state.session_id
                        }
                    )
                    
                    if response and response.status_code == 200:
                        data = response.json()
                        bot_response = data.get('response', 'Sorry, I could not generate a response.')
                        search_results = data.get('search_results', [])
                        
                        st.write(bot_response)
                        
                        # Show sources
                        if search_results:
                            with st.expander("📚 Sources"):
                                for idx, result in enumerate(search_results[:3], 1):
                                    st.markdown(f"**Source {idx}** (Score: {result.get('score', 0):.3f})")
                                    st.text(result.get('chunk_text', '')[:200] + "...")
                                    st.markdown(f"*Document: {result.get('document_id', 'N/A')}*")
                                    st.markdown("---")
                        
                        # Add to history
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': bot_response,
                            'search_results': search_results
                        })
                    else:
                        error_msg = f"❌ Could not get response: {response.status_code if response else 'No response'}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': error_msg
                        })
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': error_msg
                    })
        
        st.rerun()
    
    # Quick actions sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 Chat Actions")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
        
        st.markdown("### 💡 Example Questions")
        example_questions = [
            "What's the total amount in bank statements?",
            "Show me invoice summary",
            "Are there any anomalies?",
            "What documents are missing?",
            "Summarize my financial data"
        ]
        
        for question in example_questions:
            if st.button(f"💭 {question}", key=f"example_{question[:20]}", use_container_width=True):
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': question
                })
                st.rerun()
