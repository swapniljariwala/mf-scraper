"""
Mutual Fund Dashboard - Page 1: Category Tradeoff Explorer
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(
    page_title="MF Dashboard - Category Explorer",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_parquet('output/all_funds.parquet')
    # Fill NaN values with 0 for AUM (size of bubble)
    df['aum_cr'] = df['aum_cr'].fillna(0)
    return df

df = load_data()

# Title
st.title("📊 Mutual Fund Category Explorer")

# ===== SIDEBAR FILTERS =====
with st.sidebar:
    st.header("⚙️ Filters & Settings")
    
    # Get all categories
    all_categories = sorted(df['fund_category'].unique().tolist())
    selected_categories = all_categories  # Always show all categories in Graph 1
    
    # Return period selector
    return_period_options = {
        "1 Month": "return_1m",
        "3 Months": "return_3m", 
        "6 Months": "return_6m",
        "1 Year": "return_1y",
        "3 Years": "return_3y",
        "5 Years": "return_5y",
        "Since Inception": "return_since_inception"
    }
    
    selected_period = st.selectbox(
        "Return Period:",
        options=list(return_period_options.keys()),
        index=5  # Default to 5 Years
    )
    
    return_col = return_period_options[selected_period]
    
    st.divider()
    
    # View selector
    view_options = {
        "Return vs Risk (SD)": ("sd", "Risk-Return Tradeoff"),
        "Return vs Expense Ratio": ("expense_ratio", "Return-Cost Tradeoff"),
        "Sharpe vs Expense Ratio": ("expense_ratio", "Value Sweet Spot"),
        "Alpha vs Beta": ("beta", "Excess Return vs Market Sensitivity")
    }

    selected_view = st.selectbox(
        "View Type:",
        options=list(view_options.keys()),
        index=0
    )

# ===== HELPER FUNCTIONS =====
def get_filtered_data(dataframe, x_col, y_col):
    """Filter data based on selected view (drop rows with NaN in x or y axis)"""
    return dataframe.dropna(subset=[x_col, y_col, 'aum_cr'])

# Get axis configuration
x_col, title_suffix = view_options[selected_view]

# Set y-axis based on view type
if selected_view == "Sharpe vs Expense Ratio":
    y_col = "sharpe"
elif selected_view == "Alpha vs Beta":
    y_col = "alpha"
else:
    y_col = return_col

# ===== GRAPH 1: CATEGORY AGGREGATES =====
st.subheader("📈 Graph 1: Category Comparison (AUM-Weighted Averages)")

# Filter dataframe by selected categories
df_filtered_categories = df[df['fund_category'].isin(selected_categories)]
df_cat = get_filtered_data(df_filtered_categories, x_col, y_col)

# Aggregate by category using AUM-weighted averages
def weighted_avg(group, col):
    weights = group['aum_cr']
    return (group[col] * weights).sum() / weights.sum() if weights.sum() > 0 else group[col].mean()

category_stats = df_cat.groupby('fund_category').apply(
    lambda g: pd.Series({
        x_col: weighted_avg(g, x_col),
        y_col: weighted_avg(g, y_col),
        'aum_cr': g['aum_cr'].sum(),
        'sharpe': weighted_avg(g, 'sharpe'),
        'expense_ratio': weighted_avg(g, 'expense_ratio'),
        'sd': weighted_avg(g, 'sd'),
        'num_funds': len(g),
        'return_1y': weighted_avg(g, 'return_1y'),
        'return_3y': weighted_avg(g, 'return_3y'),
        'return_5y': weighted_avg(g, 'return_5y')
    })
).reset_index()

fig1 = px.scatter(
    category_stats,
    x=x_col,
    y=y_col,
    size="aum_cr",
    color="fund_category",
    text="fund_category",
    hover_data={
        "fund_category": True,
        "num_funds": True,
        "return_1y": ":.2f",
        "return_3y": ":.2f",
        "return_5y": ":.2f",
        "sharpe": ":.2f",
        "expense_ratio": ":.2f",
        "sd": ":.2f",
        "aum_cr": ":.0f",
        x_col: ":.2f",
        y_col: ":.2f"
    },
    title=f"{title_suffix} - Category Averages",
    labels={
        "sd": "Avg Risk (SD)",
        "return_1y": "Avg 1Y Return (%)",
        "return_3y": "Avg 3Y Return (%)",
        "return_5y": "Avg 5Y Return (%)",
        "expense_ratio": "Avg Expense Ratio (%)",
        "sharpe": "Avg Sharpe Ratio",
        "alpha": "Avg Alpha",
        "beta": "Avg Beta",
        "aum_cr": "Total AUM (Cr)",
        "fund_category": "Category",
        "num_funds": "# of Funds"
    },
    size_max=60
)

# Add category labels on the plot
fig1.update_traces(textposition='top center', textfont_size=10)
fig1.update_layout(height=500, hovermode='closest')

st.plotly_chart(fig1, use_container_width=True)

# ===== BOX PLOTS: DISTRIBUTION ANALYSIS =====
st.subheader("📦 Distribution Analysis by Category")

# Create tabs for different metric groups
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Returns", "⚖️ Risk-Adjusted Returns", "⚠️ Risk Metrics", "💰 Cost", "📊 Fund Size"])

with tab1:
    st.markdown("### Return Distribution Across Categories")
    
    # Calculate median order for sorting
    category_order_5y = df_filtered_categories.groupby('fund_category')['return_5y'].median().sort_values(ascending=False).index.tolist()
    category_order_3y = df_filtered_categories.groupby('fund_category')['return_3y'].median().sort_values(ascending=False).index.tolist()
    category_order_1y = df_filtered_categories.groupby('fund_category')['return_1y'].median().sort_values(ascending=False).index.tolist()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_ret5y = px.box(
            df_filtered_categories,
            x="fund_category",
            y="return_5y",
            color="fund_category",
            title="5-Year Returns",
            labels={"fund_category": "Category", "return_5y": "5Y Return (%)"}
        )
        fig_ret5y.update_xaxes(categoryorder='array', categoryarray=category_order_5y)
        fig_ret5y.update_layout(showlegend=False, xaxis={'tickangle': 45})
        st.plotly_chart(fig_ret5y, use_container_width=True)
    
    with col2:
        fig_ret3y = px.box(
            df_filtered_categories,
            x="fund_category",
            y="return_3y",
            color="fund_category",
            title="3-Year Returns",
            labels={"fund_category": "Category", "return_3y": "3Y Return (%)"}
        )
        fig_ret3y.update_xaxes(categoryorder='array', categoryarray=category_order_3y)
        fig_ret3y.update_layout(showlegend=False, xaxis={'tickangle': 45})
        st.plotly_chart(fig_ret3y, use_container_width=True)
    
    with col3:
        fig_ret1y = px.box(
            df_filtered_categories,
            x="fund_category",
            y="return_1y",
            color="fund_category",
            title="1-Year Returns",
            labels={"fund_category": "Category", "return_1y": "1Y Return (%)"}
        )
        fig_ret1y.update_xaxes(categoryorder='array', categoryarray=category_order_1y)
        fig_ret1y.update_layout(showlegend=False, xaxis={'tickangle': 45})
        st.plotly_chart(fig_ret1y, use_container_width=True)

with tab2:
    st.markdown("### Risk-Adjusted Return Distribution Across Categories")
    category_order_sharpe = df_filtered_categories.groupby('fund_category')['sharpe'].median().sort_values(ascending=False).index.tolist()
    
    fig_sharpe = px.box(
        df_filtered_categories,
        x="fund_category",
        y="sharpe",
        color="fund_category",
        title="Sharpe Ratio (Return per Unit Risk)",
        labels={"fund_category": "Category", "sharpe": "Sharpe Ratio"}
    )
    fig_sharpe.update_xaxes(categoryorder='array', categoryarray=category_order_sharpe)
    fig_sharpe.update_layout(showlegend=False, xaxis={'tickangle': 45}, height=500)
    st.plotly_chart(fig_sharpe, use_container_width=True)
    
    st.caption("💡 **Sharpe Ratio** = Risk-adjusted return. Higher is better. Combines return and risk into single metric.")

with tab3:
    st.markdown("### Risk Metrics Distribution Across Categories")
    col1, col2 = st.columns(2)
    
    category_order_sd = df_filtered_categories.groupby('fund_category')['sd'].median().sort_values().index.tolist()
    category_order_beta = df_filtered_categories.groupby('fund_category')['beta'].median().sort_values().index.tolist()
    
    with col1:
        fig_sd = px.box(
            df_filtered_categories,
            x="fund_category",
            y="sd",
            color="fund_category",
            title="Standard Deviation (Volatility)",
            labels={"fund_category": "Category", "sd": "SD (%)"}
        )
        fig_sd.update_xaxes(categoryorder='array', categoryarray=category_order_sd)
        fig_sd.update_layout(showlegend=False, xaxis={'tickangle': 45})
        st.plotly_chart(fig_sd, use_container_width=True)
    
    with col2:
        fig_beta = px.box(
            df_filtered_categories,
            x="fund_category",
            y="beta",
            color="fund_category",
            title="Beta (Market Sensitivity)",
            labels={"fund_category": "Category", "beta": "Beta"}
        )
        fig_beta.update_xaxes(categoryorder='array', categoryarray=category_order_beta)
        fig_beta.update_layout(showlegend=False, xaxis={'tickangle': 45})
        st.plotly_chart(fig_beta, use_container_width=True)

with tab4:
    st.markdown("### Expense Ratio Distribution Across Categories")
    category_order_expense = df_filtered_categories.groupby('fund_category')['expense_ratio'].median().sort_values().index.tolist()
    
    fig_expense = px.box(
        df_filtered_categories,
        x="fund_category",
        y="expense_ratio",
        color="fund_category",
        title="Expense Ratio",
        labels={"fund_category": "Category", "expense_ratio": "Expense Ratio (%)"}
    )
    fig_expense.update_xaxes(categoryorder='array', categoryarray=category_order_expense)
    fig_expense.update_layout(showlegend=False, xaxis={'tickangle': 45}, height=500)
    st.plotly_chart(fig_expense, use_container_width=True)

with tab5:
    st.markdown("### AUM Distribution Across Categories")
    category_order_aum = df_filtered_categories.groupby('fund_category')['aum_cr'].median().sort_values(ascending=False).index.tolist()
    
    fig_aum = px.box(
        df_filtered_categories,
        x="fund_category",
        y="aum_cr",
        color="fund_category",
        title="Assets Under Management",
        labels={"fund_category": "Category", "aum_cr": "AUM (Crores)"},
        log_y=True  # Use log scale due to wide range
    )
    fig_aum.update_xaxes(categoryorder='array', categoryarray=category_order_aum)
    fig_aum.update_layout(showlegend=False, xaxis={'tickangle': 45}, height=500)
    st.plotly_chart(fig_aum, use_container_width=True)
