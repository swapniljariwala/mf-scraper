"""
Mutual Fund Dashboard - Page 2: Efficient Frontier Analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(page_title="MF Dashboard - Efficient Frontier", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_parquet('output/all_funds.parquet')
    df['aum_cr'] = df['aum_cr'].fillna(0)
    return df

df = load_data()

# Title
st.title("🎯 Efficient Frontier Analysis")
st.markdown("Identify Pareto-optimal funds within a category - funds with the best risk-return tradeoffs")

# ===== SIDEBAR FILTERS =====
with st.sidebar:
    st.header("⚙️ Filters & Settings")
    
    # Category selector
    all_categories = sorted(df['fund_category'].unique().tolist())
    default_index = all_categories.index('flexi-cap') if 'flexi-cap' in all_categories else 0
    single_category = st.selectbox(
        "Select Category:",
        options=all_categories,
        index=default_index
    )
    
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
    
    st.markdown("---")
    st.subheader("Filters")
    
    # Calculate dynamic ranges from data
    data_return_min = float(df[return_col].min())
    data_return_max = float(df[return_col].max()) + 1
    data_sd_max = float(df['sd'].max()) + 1
    data_aum_min = float(df['aum_cr'].min())
    data_aum_max = float(df['aum_cr'].max()) + 1
    data_expense_max = float(df['expense_ratio'].max()) + 1
    data_age_max = float(df['fund_age_years'].max()) + 1
    
    # Return range filter
    min_return = st.slider(
        "Min Return (%):",
        min_value=data_return_min,
        max_value=data_return_max,
        value=data_return_min,
        step=1.0
    )
    
    max_return = st.slider(
        "Max Return (%):",
        min_value=data_return_min,
        max_value=data_return_max,
        value=data_return_max,
        step=1.0
    )
    
    # Risk (SD) filter
    max_sd = st.slider(
        "Max Risk - SD (%):",
        min_value=0.0,
        max_value=data_sd_max,
        value=data_sd_max,
        step=1.0
    )
    
    # AUM range filter
    min_aum = st.slider(
        "Min AUM (Crores):",
        min_value=data_aum_min,
        max_value=data_aum_max,
        value=data_aum_min,
        step=100.0
    )
    
    max_aum = st.slider(
        "Max AUM (Crores):",
        min_value=data_aum_min,
        max_value=data_aum_max,
        value=data_aum_max,
        step=500.0
    )
    
    # Expense ratio filter
    max_expense = st.slider(
        "Max Expense Ratio (%):",
        min_value=0.0,
        max_value=data_expense_max,
        value=data_expense_max,
        step=0.1
    )
    
    # Fund age filter
    min_age = st.slider(
        "Min Fund Age (Years):",
        min_value=0.0,
        max_value=data_age_max,
        value=0.0,
        step=0.5
    )

# ===== HELPER FUNCTIONS =====
def get_filtered_data(dataframe, x_col, y_col):
    """Filter data based on selected view (drop rows with NaN in x or y axis)"""
    return dataframe.dropna(subset=[x_col, y_col, 'aum_cr'])

def is_pareto_efficient(df, x_col, y_col):
    """
    Identify Pareto-efficient points (non-dominated solutions)
    For risk-return: minimize x (risk), maximize y (return)
    """
    is_efficient = []
    for i in range(len(df)):
        # Check if this point is dominated by any other point
        dominated = False
        for j in range(len(df)):
            if i != j:
                # Point i is dominated if point j has:
                # - Lower or equal risk (x) AND higher return (y)
                # - OR lower risk (x) AND equal or higher return (y)
                if (df.iloc[j][x_col] <= df.iloc[i][x_col] and 
                    df.iloc[j][y_col] > df.iloc[i][y_col]) or \
                   (df.iloc[j][x_col] < df.iloc[i][x_col] and 
                    df.iloc[j][y_col] >= df.iloc[i][y_col]):
                    dominated = True
                    break
        is_efficient.append(not dominated)
    return is_efficient

# Get axis configuration
x_col, title_suffix = view_options[selected_view]

# Set y-axis based on view type
if selected_view == "Sharpe vs Expense Ratio":
    y_col = "sharpe"
elif selected_view == "Alpha vs Beta":
    y_col = "alpha"
else:
    y_col = return_col

# ===== EFFICIENT FRONTIER VISUALIZATION =====
st.subheader(f"📊 {single_category} - {title_suffix}")

# Filter for single category
df_single = df[df['fund_category'] == single_category]
df_single = get_filtered_data(df_single, x_col, y_col)

# Apply user filters
df_single = df_single[
    (df_single[y_col] >= min_return) &
    (df_single[y_col] <= max_return) &
    (df_single['sd'] <= max_sd) &
    (df_single['aum_cr'] >= min_aum) &
    (df_single['aum_cr'] <= max_aum) &
    (df_single['expense_ratio'] <= max_expense) &
    (df_single['fund_age_years'] >= min_age)
]

# Show filter summary
if len(df_single) == 0:
    st.warning("⚠️ No funds match the current filter criteria. Please adjust the filters.")
    st.stop()
else:
    st.caption(f"Showing **{len(df_single)}** funds after applying filters")

# Calculate Pareto frontier
df_single['is_efficient'] = is_pareto_efficient(df_single, x_col, y_col)
df_single['frontier_status'] = df_single['is_efficient'].map({True: 'Efficient Frontier', False: 'Dominated'})

fig = px.scatter(
    df_single,
    x=x_col,
    y=y_col,
    size="aum_cr",
    color="frontier_status",
    symbol="frontier_status",
    hover_name="fund_name",
    hover_data={
        "return_1y": ":.2f",
        "return_3y": ":.2f",
        "return_5y": ":.2f",
        "sharpe": ":.2f",
        "expense_ratio": ":.2f",
        "sd": ":.2f",
        "aum_cr": ":.0f",
        "is_efficient": False,
        "frontier_status": True,
        x_col: ":.2f",
        y_col: ":.2f"
    },
    title=f"Pareto-Efficient Frontier Analysis",
    labels={
        "sd": "Standard Deviation (Risk)",
        "return_1y": "1-Year Return (%)",
        "return_3y": "3-Year Return (%)",
        "return_5y": "5-Year Return (%)",
        "expense_ratio": "Expense Ratio (%)",
        "sharpe": "Sharpe Ratio",
        "alpha": "Alpha",
        "beta": "Beta",
        "aum_cr": "AUM (Crores)",
        "frontier_status": "Status"
    },
    color_discrete_map={"Efficient Frontier": "#00CC96", "Dominated": "#636EFA"},
    size_max=30
)

fig.update_layout(
    height=600, 
    hovermode='closest',
    legend=dict(
        title="Fund Status",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

# Show frontier statistics
efficient_count = df_single['is_efficient'].sum()
total_count = len(df_single)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Funds", total_count)
with col2:
    st.metric("Efficient Frontier Funds", efficient_count)
with col3:
    st.metric("Efficiency Rate", f"{efficient_count/total_count*100:.1f}%")

# ===== EFFICIENT FUNDS TABLE =====
st.subheader("✅ Funds on Efficient Frontier")

# Filter and display efficient funds
efficient_funds = df_single[df_single['is_efficient']].copy()
efficient_funds = efficient_funds.sort_values(by=y_col, ascending=False)

# Select columns to display
display_cols = ['fund_name', 'return_1y', 'return_3y', 'return_5y', 'sd', 'sharpe', 'expense_ratio', 'aum_cr']
display_df = efficient_funds[display_cols].copy()

# Rename columns for display
display_df.columns = ['Fund Name', '1Y Return (%)', '3Y Return (%)', '5Y Return (%)', 
                      'Risk (SD)', 'Sharpe', 'Expense (%)', 'AUM (Cr)']

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fund Name": st.column_config.TextColumn(width="large"),
        "1Y Return (%)": st.column_config.NumberColumn(format="%.2f"),
        "3Y Return (%)": st.column_config.NumberColumn(format="%.2f"),
        "5Y Return (%)": st.column_config.NumberColumn(format="%.2f"),
        "Risk (SD)": st.column_config.NumberColumn(format="%.2f"),
        "Sharpe": st.column_config.NumberColumn(format="%.2f"),
        "Expense (%)": st.column_config.NumberColumn(format="%.2f"),
        "AUM (Cr)": st.column_config.NumberColumn(format="%.0f"),
    }
)

# Info box
with st.expander("ℹ️ What is the Efficient Frontier?"):
    st.markdown("""
    **Efficient Frontier** identifies funds that are **Pareto-optimal** - meaning:
    
    - ✅ **No other fund** offers both lower risk AND higher return simultaneously
    - ✅ These funds represent the **best risk-return tradeoffs** in the category
    - ❌ **Dominated funds** can be improved by switching to a frontier fund
    
    **How to use:**
    - 🟢 **Green points** = Efficient frontier (optimal choices)
    - 🔵 **Blue points** = Dominated funds (sub-optimal)
    
    Focus your fund selection on the green points for the best value!
    """)
