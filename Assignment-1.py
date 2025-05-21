import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Data Models
@dataclass
class Policyholder:
    id: str
    name: str
    age: int
    policy_type: str
    sum_insured: float
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Claim:
    id: str
    policyholder_id: str
    claim_amount: float
    reason: str
    status: str
    date_of_claim: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

# Data Manager Class
class InsuranceDataManager:
    def __init__(self):
        self.policyholders: Dict[str, Policyholder] = {}
        self.claims: Dict[str, Claim] = {}
        self.data_file = "insurance_data.json"
        self.load_data()
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            data = {
                'policyholders': {k: v.to_dict() for k, v in self.policyholders.items()},
                'claims': {k: v.to_dict() for k, v in self.claims.items()}
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
    
    def load_data(self):
        """Load data from JSON file"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.policyholders = {
                    k: Policyholder.from_dict(v) 
                    for k, v in data.get('policyholders', {}).items()
                }
                self.claims = {
                    k: Claim.from_dict(v) 
                    for k, v in data.get('claims', {}).items()
                }
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    def add_policyholder(self, name: str, age: int, policy_type: str, sum_insured: float) -> str:
        """Add a new policyholder"""
        if not name or age <= 0 or sum_insured <= 0:
            raise ValueError("Invalid input: Name cannot be empty, age and sum insured must be positive")
        
        policyholder_id = str(uuid.uuid4())
        self.policyholders[policyholder_id] = Policyholder(
            id=policyholder_id,
            name=name,
            age=age,
            policy_type=policy_type,
            sum_insured=sum_insured
        )
        self.save_data()
        return policyholder_id
    
    def add_claim(self, policyholder_id: str, claim_amount: float, reason: str, status: str = "Pending") -> str:
        """Add a new claim"""
        if policyholder_id not in self.policyholders:
            raise ValueError("Policyholder not found")
        
        if claim_amount <= 0:
            raise ValueError("Claim amount must be positive")
        
        claim_id = str(uuid.uuid4())
        self.claims[claim_id] = Claim(
            id=claim_id,
            policyholder_id=policyholder_id,
            claim_amount=claim_amount,
            reason=reason,
            status=status,
            date_of_claim=datetime.now().strftime("%Y-%m-%d")
        )
        self.save_data()
        return claim_id
    
    def update_claim_status(self, claim_id: str, status: str):
        """Update claim status"""
        if claim_id not in self.claims:
            raise ValueError("Claim not found")
        
        self.claims[claim_id].status = status
        self.save_data()
    
    def get_claims_by_policyholder(self, policyholder_id: str) -> List[Claim]:
        """Get all claims for a specific policyholder"""
        return [claim for claim in self.claims.values() if claim.policyholder_id == policyholder_id]
    
    def calculate_claim_frequency(self, policyholder_id: str, days: int = 365) -> int:
        """Calculate claim frequency for a policyholder in the last specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        claims = self.get_claims_by_policyholder(policyholder_id)
        
        recent_claims = [
            claim for claim in claims 
            if datetime.strptime(claim.date_of_claim, "%Y-%m-%d") >= cutoff_date
        ]
        return len(recent_claims)
    
    def get_high_risk_policyholders(self) -> List[Dict]:
        """Identify high-risk policyholders"""
        high_risk = []
        
        for policyholder_id, policyholder in self.policyholders.items():
            claims = self.get_claims_by_policyholder(policyholder_id)
            claim_frequency = self.calculate_claim_frequency(policyholder_id)
            total_claim_amount = sum(claim.claim_amount for claim in claims)
            claim_ratio = total_claim_amount / policyholder.sum_insured
            
            risk_factors = []
            if claim_frequency > 3:
                risk_factors.append(f"High frequency: {claim_frequency} claims")
            if claim_ratio > 0.8:
                risk_factors.append(f"High claim ratio: {claim_ratio:.2%}")
            
            if risk_factors:
                high_risk.append({
                    'policyholder': policyholder,
                    'claim_frequency': claim_frequency,
                    'total_claims': total_claim_amount,
                    'claim_ratio': claim_ratio,
                    'risk_factors': risk_factors
                })
        
        return high_risk

# Risk Analysis Module
class RiskAnalyzer:
    def __init__(self, data_manager: InsuranceDataManager):
        self.data_manager = data_manager
    
    def get_claims_by_policy_type(self) -> Dict[str, Dict]:
        """Aggregate claims by policy type"""
        policy_claims = {}
        
        for claim in self.data_manager.claims.values():
            policyholder = self.data_manager.policyholders[claim.policyholder_id]
            policy_type = policyholder.policy_type
            
            if policy_type not in policy_claims:
                policy_claims[policy_type] = {
                    'count': 0,
                    'total_amount': 0,
                    'pending': 0,
                    'approved': 0,
                    'rejected': 0
                }
            
            policy_claims[policy_type]['count'] += 1
            policy_claims[policy_type]['total_amount'] += claim.claim_amount
            policy_claims[policy_type][claim.status.lower()] += 1
        
        return policy_claims

# Reports Module
class ReportsGenerator:
    def __init__(self, data_manager: InsuranceDataManager):
        self.data_manager = data_manager
    
    def get_monthly_claims(self) -> Dict[str, int]:
        """Get total claims per month"""
        monthly_claims = {}
        
        for claim in self.data_manager.claims.values():
            month_year = datetime.strptime(claim.date_of_claim, "%Y-%m-%d").strftime("%Y-%m")
            monthly_claims[month_year] = monthly_claims.get(month_year, 0) + 1
        
        return monthly_claims
    
    def get_average_claim_by_policy_type(self) -> Dict[str, float]:
        """Calculate average claim amount by policy type"""
        policy_totals = {}
        policy_counts = {}
        
        for claim in self.data_manager.claims.values():
            policyholder = self.data_manager.policyholders[claim.policyholder_id]
            policy_type = policyholder.policy_type
            
            policy_totals[policy_type] = policy_totals.get(policy_type, 0) + claim.claim_amount
            policy_counts[policy_type] = policy_counts.get(policy_type, 0) + 1
        
        return {
            policy_type: policy_totals[policy_type] / policy_counts[policy_type]
            for policy_type in policy_totals
        }
    
    def get_highest_claim(self) -> Optional[Claim]:
        """Get the highest claim filed"""
        if not self.data_manager.claims:
            return None
        
        return max(self.data_manager.claims.values(), key=lambda x: x.claim_amount)
    
    def get_pending_claims(self) -> List[Dict]:
        """Get list of policyholders with pending claims"""
        pending_claims = []
        
        for claim in self.data_manager.claims.values():
            if claim.status.lower() == 'pending':
                policyholder = self.data_manager.policyholders[claim.policyholder_id]
                pending_claims.append({
                    'claim': claim,
                    'policyholder': policyholder
                })
        
        return pending_claims

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = InsuranceDataManager()

# Streamlit App
def main():
    st.set_page_config(
        page_title="Insurance Claims Management",
        page_icon="🛡️",
        layout="wide"
    )
    
    st.title("🛡️ Insurance Claims Management System")
    st.sidebar.title("Navigation")
    
    # Navigation
    pages = {
        "Dashboard": dashboard_page,
        "Policyholder Management": policyholder_management_page,
        "Claim Management": claim_management_page,
        "Risk Analysis": risk_analysis_page,
        "Reports": reports_page
    }
    
    selected_page = st.sidebar.selectbox("Select Page", list(pages.keys()))
    
    # Display selected page
    pages[selected_page]()

def dashboard_page():
    st.header("📊 Dashboard")
    
    data_manager = st.session_state.data_manager
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Policyholders", len(data_manager.policyholders))
    
    with col2:
        st.metric("Total Claims", len(data_manager.claims))
    
    with col3:
        pending_claims = sum(1 for claim in data_manager.claims.values() if claim.status.lower() == 'pending')
        st.metric("Pending Claims", pending_claims)
    
    with col4:
        total_claim_amount = sum(claim.claim_amount for claim in data_manager.claims.values())
        st.metric("Total Claim Amount", f"${total_claim_amount:,.2f}")
    
    # Charts
    if data_manager.claims:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Claims by Status")
            status_counts = {}
            for claim in data_manager.claims.values():
                status_counts[claim.status] = status_counts.get(claim.status, 0) + 1
            
            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Claims by Policy Type")
            risk_analyzer = RiskAnalyzer(data_manager)
            policy_claims = risk_analyzer.get_claims_by_policy_type()
            
            if policy_claims:
                policy_types = list(policy_claims.keys())
                claim_counts = [policy_claims[pt]['count'] for pt in policy_types]
                
                fig = px.bar(x=policy_types, y=claim_counts)
                fig.update_layout(xaxis_title="Policy Type", yaxis_title="Number of Claims")
                st.plotly_chart(fig, use_container_width=True)

def policyholder_management_page():
    st.header("👥 Policyholder Management")
    
    data_manager = st.session_state.data_manager
    
    # Add new policyholder
    st.subheader("Add New Policyholder")
    
    with st.form("add_policyholder"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*")
            age = st.number_input("Age*", min_value=1, max_value=120, value=30)
        
        with col2:
            policy_type = st.selectbox("Policy Type*", ["Health", "Vehicle", "Life"])
            sum_insured = st.number_input("Sum Insured*", min_value=0.01, value=10000.0)
        
        if st.form_submit_button("Add Policyholder"):
            try:
                policyholder_id = data_manager.add_policyholder(name, age, policy_type, sum_insured)
                st.success(f"Policyholder added successfully! ID: {policyholder_id}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    
    # Display existing policyholders
    st.subheader("Existing Policyholders")
    
    if data_manager.policyholders:
        policyholders_data = []
        for ph in data_manager.policyholders.values():
            claims_count = len(data_manager.get_claims_by_policyholder(ph.id))
            policyholders_data.append({
                "ID": ph.id,
                "Name": ph.name,
                "Age": ph.age,
                "Policy Type": ph.policy_type,
                "Sum Insured": f"${ph.sum_insured:,.2f}",
                "Total Claims": claims_count
            })
        
        df = pd.DataFrame(policyholders_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No policyholders registered yet.")

def claim_management_page():
    st.header("📋 Claim Management")
    
    data_manager = st.session_state.data_manager
    
    # Add new claim
    st.subheader("Add New Claim")
    
    if not data_manager.policyholders:
        st.warning("Please add policyholders first before creating claims.")
        return
    
    with st.form("add_claim"):
        col1, col2 = st.columns(2)
        
        with col1:
            policyholder_options = {f"{ph.name} (ID: {ph.id})": ph.id for ph in data_manager.policyholders.values()}
            selected_policyholder = st.selectbox("Select Policyholder*", list(policyholder_options.keys()))
            claim_amount = st.number_input("Claim Amount*", min_value=0.01, value=1000.0)
        
        with col2:
            reason = st.text_area("Reason*")
            status = st.selectbox("Status", ["Pending", "Approved", "Rejected"])
        
        if st.form_submit_button("Add Claim"):
            try:
                policyholder_id = policyholder_options[selected_policyholder]
                claim_id = data_manager.add_claim(policyholder_id, claim_amount, reason, status)
                st.success(f"Claim added successfully! ID: {claim_id}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    
    # Update claim status
    st.subheader("Update Claim Status")
    
    if data_manager.claims:
        claim_options = {f"Claim {claim.id[:8]}... - ${claim.claim_amount}": claim.id for claim in data_manager.claims.values()}
        selected_claim = st.selectbox("Select Claim", list(claim_options.keys()))
        new_status = st.selectbox("New Status", ["Pending", "Approved", "Rejected"])
        
        if st.button("Update Status"):
            try:
                claim_id = claim_options[selected_claim]
                data_manager.update_claim_status(claim_id, new_status)
                st.success("Claim status updated successfully!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    
    # Display existing claims
    st.subheader("Existing Claims")
    
    if data_manager.claims:
        claims_data = []
        for claim in data_manager.claims.values():
            policyholder = data_manager.policyholders[claim.policyholder_id]
            claims_data.append({
                "Claim ID": claim.id,
                "Policyholder": policyholder.name,
                "Amount": f"${claim.claim_amount:,.2f}",
                "Reason": claim.reason[:50] + "..." if len(claim.reason) > 50 else claim.reason,
                "Status": claim.status,
                "Date": claim.date_of_claim
            })
        
        df = pd.DataFrame(claims_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No claims registered yet.")

def risk_analysis_page():
    st.header("⚠️ Risk Analysis")
    
    data_manager = st.session_state.data_manager
    risk_analyzer = RiskAnalyzer(data_manager)
    
    # High-risk policyholders
    st.subheader("High-Risk Policyholders")
    high_risk = data_manager.get_high_risk_policyholders()
    
    if high_risk:
        for risk_data in high_risk:
            ph = risk_data['policyholder']
            with st.expander(f"⚠️ {ph.name} - Risk Score: {len(risk_data['risk_factors'])}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Policy Type:** {ph.policy_type}")
                    st.write(f"**Claim Frequency:** {risk_data['claim_frequency']} claims/year")
                    st.write(f"**Total Claims:** ${risk_data['total_claims']:,.2f}")
                
                with col2:
                    st.write(f"**Sum Insured:** ${ph.sum_insured:,.2f}")
                    st.write(f"**Claim Ratio:** {risk_data['claim_ratio']:.2%}")
                    st.write("**Risk Factors:**")
                    for factor in risk_data['risk_factors']:
                        st.write(f"• {factor}")
    else:
        st.success("No high-risk policyholders identified!")
    
    # Claims by policy type
    st.subheader("Claims Analysis by Policy Type")
    policy_claims = risk_analyzer.get_claims_by_policy_type()
    
    if policy_claims:
        for policy_type, data in policy_claims.items():
            with st.expander(f"{policy_type} Insurance"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Claims", data['count'])
                
                with col2:
                    st.metric("Total Amount", f"${data['total_amount']:,.2f}")
                
                with col3:
                    avg_amount = data['total_amount'] / data['count'] if data['count'] > 0 else 0
                    st.metric("Average Claim", f"${avg_amount:,.2f}")
                
                with col4:
                    approval_rate = data['approved'] / data['count'] * 100 if data['count'] > 0 else 0
                    st.metric("Approval Rate", f"{approval_rate:.1f}%")

def reports_page():
    st.header("📈 Reports")
    
    data_manager = st.session_state.data_manager
    reports_generator = ReportsGenerator(data_manager)
    
    # Monthly claims chart
    st.subheader("Claims Trend Over Time")
    monthly_claims = reports_generator.get_monthly_claims()
    
    if monthly_claims:
        months = sorted(monthly_claims.keys())
        claims_count = [monthly_claims[month] for month in months]
        
        fig = px.line(x=months, y=claims_count, title="Monthly Claims Trend")
        fig.update_layout(xaxis_title="Month", yaxis_title="Number of Claims")
        st.plotly_chart(fig, use_container_width=True)
    
    # Average claim by policy type
    st.subheader("Average Claim Amount by Policy Type")
    avg_claims = reports_generator.get_average_claim_by_policy_type()
    
    if avg_claims:
        col1, col2 = st.columns(2)
        
        with col1:
            for policy_type, avg_amount in avg_claims.items():
                st.metric(f"{policy_type} Insurance", f"${avg_amount:,.2f}")
        
        with col2:
            fig = px.bar(x=list(avg_claims.keys()), y=list(avg_claims.values()),
                        title="Average Claim Amount by Policy Type")
            fig.update_layout(xaxis_title="Policy Type", yaxis_title="Average Claim Amount ($)")
            st.plotly_chart(fig, use_container_width=True)
    
    # Highest claim
    st.subheader("Highest Claim Filed")
    highest_claim = reports_generator.get_highest_claim()
    
    if highest_claim:
        policyholder = data_manager.policyholders[highest_claim.policyholder_id]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Amount", f"${highest_claim.claim_amount:,.2f}")
        
        with col2:
            st.metric("Policyholder", policyholder.name)
        
        with col3:
            st.metric("Date", highest_claim.date_of_claim)
        
        st.write(f"**Reason:** {highest_claim.reason}")
    
    # Pending claims
    st.subheader("Policyholders with Pending Claims")
    pending_claims = reports_generator.get_pending_claims()
    
    if pending_claims:
        pending_data = []
        for item in pending_claims:
            pending_data.append({
                "Policyholder": item['policyholder'].name,
                "Policy Type": item['policyholder'].policy_type,
                "Claim Amount": f"${item['claim'].claim_amount:,.2f}",
                "Date Filed": item['claim'].date_of_claim,
                "Reason": item['claim'].reason[:50] + "..." if len(item['claim'].reason) > 50 else item['claim'].reason
            })
        
        df = pd.DataFrame(pending_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No pending claims found.")

if __name__ == "__main__":
    main()