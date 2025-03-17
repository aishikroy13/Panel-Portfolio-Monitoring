import panel as pn
import pandas as pd
import numpy as np
import altair as alt
import holoviews as hv
import os

import altair as alt
alt.renderers.enable('default')

# Enable Panel extensions
pn.extension('vega')

# Load the analyzed data
df = pd.read_csv("data/analyzed_portfolio.csv")
# Initialize filtered_df right after loading the data
filtered_df = df.copy()

# Custom Colors for Traffic Light System
colors = {
    "Green": "#00FF00",  # Bright Green
    "Yellow": "#FFFF00",  # Bright Yellow
    "Amber": "#FFA500",   # Orange (Amber)
    "Red": "#FF0000"      # Bright Red
}

# Add Sector column to the DataFrame
df["Sector"] = df["Company"].map({
    "TWLO": "Technology", "PD": "Technology", "BOX": "Technology",
    "TDOC": "Healthcare", "AMWL": "Healthcare", "HIMS": "Healthcare",
    "MAN": "Services", "RHI": "Services", "ASGN": "Services"
})

# Qualitative notes for companies
qualitative_notes = {
    "TWLO": "Facing competition from new entrants.",
    "PD": "Negative EBITDA due to R&D investments.",
    "BOX": "Stable but high leverage from acquisition.",
    "TDOC": "Regulatory uncertainty in telehealth.",
    "AMWL": "Cash burn from expansion efforts.",
    "HIMS": "Strong growth but unproven scalability.",
    "MAN": "Cyclical risks in staffing market.",
    "RHI": "Resilient despite economic slowdown.",
    "ASGN": "Consistent performance with low debt."
}

# Portfolio Overview - Bar Chart
def create_overview_chart():
    total_assets = len(df)
    risk_distribution = df["Category"].value_counts()
    chart_data = pd.DataFrame({
        "Category": risk_distribution.index,
        "Count": risk_distribution.values
    })
    chart_data["Color"] = chart_data["Category"].map(colors)
    
    bar_chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Count:Q", title="Number of Companies"),
        y=alt.Y("Category:N", title="Category"),
        color=alt.Color("Color:N", scale=None, legend=None)
    ).properties(
        width=600,
        height=300
    )
    
    return pn.Column(
        pn.pane.Markdown("# Private Credit Portfolio Monitoring Dashboard"),
        pn.pane.Markdown("Interactive dashboard to monitor a hypothetical direct lending portfolio of 9 companies."),
        pn.pane.Markdown("## Portfolio Overview"),
        pn.pane.Markdown(f"**Total Assets:** {total_assets}"),
        pn.pane.Vega(bar_chart)
    )

# Create filter widgets
category_filter = pn.widgets.Select(
    name="Filter by Category", 
    options=["All"] + list(df["Category"].unique()), 
    value="All"
)

sector_filter = pn.widgets.MultiChoice(
    name="Filter by Sector", 
    options=["All"] + list(df["Sector"].unique()), 
    value=["All"]
)

# Filter Data based on selections
def filter_data(category, sectors):
    if category == "All":
        filtered = df.copy()
    else:
        filtered = df[df["Category"] == category].copy()
    
    if "All" not in sectors and sectors:
        filtered = filtered[filtered["Sector"].isin(sectors)]
    
    return filtered

# Create dynamic company options
def get_company_options(filtered_df):
    if filtered_df.empty:
        return []
    return list(filtered_df["Company"])

# Create company selector
filtered_df_panel = pn.bind(filter_data, category_filter, sector_filter)
company_options = pn.bind(get_company_options, filtered_df_panel)

company_selector = pn.widgets.Select(
    name="Select a Company",
    options=company_options
)

# Get company data based on selection
def get_company_data(filtered_df, company):
    if filtered_df is None or filtered_df.empty or company is None:
        return pd.Series()
    
    company_data = filtered_df[filtered_df["Company"] == company]
    if company_data.empty:
        return pd.Series()
    
    return company_data.iloc[0]

# Company Details Section
company_data = pn.bind(get_company_data, filtered_df_panel, company_selector)

def create_company_details(company_data):
    if company_data is None or len(company_data) == 0:
        return pn.pane.Markdown("No company selected or no companies match the filters.")
    
    category_color = colors.get(company_data.get("Category", ""), "#FFFFFF")
    company_name = company_data.get("Company", "")
    
    financial_data = pn.GridBox(
        pn.pane.Markdown(f"**Revenue:** ${company_data.get('Revenue', 0):,.2f}"),
        pn.pane.Markdown(f"**EBITDA:** ${company_data.get('EBITDA', 0):,.2f}"),
        pn.pane.Markdown(f"**Total Debt:** ${company_data.get('Total Debt', 0):,.2f}"),
        pn.pane.Markdown(f"**Interest Expense:** ${company_data.get('Interest Expense', 0):,.2f}"),
        pn.pane.Markdown(f"**Cash Flow:** ${company_data.get('Cash Flow from Operations', 0):,.2f}"),
        pn.pane.Markdown(f"**Leverage Ratio:** {company_data.get('Leverage Ratio', 0):.2f}"),
        ncols=3
    )
    
    other_metrics = pn.Column(
        pn.pane.Markdown(f"**Interest Coverage:** {company_data.get('Interest Coverage', 0):.2f}"),
        pn.pane.Markdown(f"**EBITDA Margin:** {company_data.get('EBITDA Margin', 0):.2%}"),
        pn.pane.HTML(f"<p><strong>Category:</strong> <span style='color:{category_color}'>{company_data.get('Category', '')}</span></p>"),
        pn.pane.Markdown(f"**Qualitative Notes:** {qualitative_notes.get(company_name, 'No notes available.')}")
    )
    
    export_button = pn.widgets.Button(name="Export Company Data to CSV", button_type="primary")
    
    def export_data(event):
    if company_name:
        try:
            csv_data = pd.Series(company_data).to_frame().T.to_csv(index=False)
            return pn.pane.HTML(f"""
            <a href="data:text/csv;charset=utf-8,{csv_data}" 
               download="{company_name}_export.csv" 
               class="pn-button bk-btn bk-btn-success">
               Download {company_name} Data
            </a>
            """)
        except Exception as e:
            return pn.pane.Alert(f"Error generating data: {str(e)}", alert_type="danger")
    return pn.pane.Alert("No company selected", alert_type="warning")
    
    export_button.on_click(export_data)
    
    export_result = pn.bind(lambda: None)  # Placeholder for export result
    
    return pn.Column(
        pn.pane.Markdown(f"## {company_name} Financial Health"),
        financial_data,
        other_metrics,
        export_button,
        export_result
    )

# Scenario Analysis Section
def create_scenario_analysis(company_data):
    if company_data is None or len(company_data) == 0:
        return pn.pane.Markdown("Select a company to perform scenario analysis.")
    
    interest_rate_slider = pn.widgets.FloatSlider(
        name="Change in Interest Rate (%)", 
        start=-5.0, 
        end=5.0, 
        value=0.0, 
        step=0.01
    )
    
    revenue_decline_slider = pn.widgets.FloatSlider(
        name="Revenue Decline (%)", 
        start=0.0, 
        end=50.0, 
        value=0.0, 
        step=1.0
    )
    
    def update_scenario(interest_rate_change, revenue_decline):
        # Calculate new interest expense and coverage
        interest_expense = company_data.get('Interest Expense', 0)
        ebitda = company_data.get('EBITDA', 0)
        total_debt = company_data.get('Total Debt', 0)
        
        new_interest_expense = interest_expense * (1 + interest_rate_change / 100)
        new_coverage = ebitda / new_interest_expense if new_interest_expense > 0 else float('inf')
        
        # Calculate new revenue, EBITDA, and leverage
        new_ebitda = ebitda * (1 - revenue_decline / 100)
        new_leverage = total_debt / new_ebitda if new_ebitda != 0 else float('inf')
        
        return pn.Column(
            pn.pane.Markdown(f"New Interest Coverage with {interest_rate_change:.2f}% rate change: {new_coverage:.2f}"),
            pn.pane.Markdown(f"New Leverage Ratio with {revenue_decline:.1f}% revenue decline: {new_leverage:.2f}")
        )
    
    scenario_results = pn.bind(update_scenario, interest_rate_slider, revenue_decline_slider)
    
    footnote = pn.pane.Markdown(
        "**Footnote:** The Interest Rate Slider adjusts Interest Expense to simulate market rate changes "
        "(e.g., 0.01% reflects a minor shift), recalculating Interest Coverage (EBITDA / New Interest Expense). "
        "The Revenue Decline Slider reduces Revenue and EBITDA proportionally, updating Leverage Ratio "
        "(Total Debt / New EBITDA) to model economic downturns. This is a hypothetical portfolio—adjust "
        "thresholds or add qualitative data for real-world use."
    )
    
    return pn.Column(
        pn.pane.Markdown("## Scenario Analysis"),
        pn.pane.Markdown("Simulate the impact of market changes on portfolio health."),
        interest_rate_slider,
        revenue_decline_slider,
        scenario_results,
        footnote
    )

# Performance Trends Section
def create_performance_trends(company_data):
    if company_data is None or len(company_data) == 0:
        return pn.pane.Markdown("Select a company to view performance trends.")
    
    years = ["2021", "2022", "2023"]
    
    # Generate trend data for selected company
    ebitda_value = abs(company_data.get('EBITDA', 0))
    revenue_value = company_data.get('Revenue', 0)
    company_name = company_data.get('Company', '')
    
    ebitda_fluctuation = ebitda_value * 0.1 if ebitda_value > 0 else 1000000
    
    # Use numpy's random seed to ensure consistent results
    np.random.seed(42)
    trend_data = pd.DataFrame({
        "Year": years,
        "Revenue": np.random.normal(revenue_value, abs(revenue_value * 0.1), 3),
        "EBITDA": np.random.normal(company_data.get('EBITDA', 0), ebitda_fluctuation, 3),
        "Company": [company_name] * 3
    })
    
    revenue_chart = alt.Chart(trend_data).mark_line(color="#00CED1").encode(
        x="Year",
        y="Revenue",
        tooltip=["Year", "Revenue"]
    ).properties(
        title="Revenue Trend",
        width=600,
        height=300
    )
    
    ebitda_chart = alt.Chart(trend_data).mark_line(color="#FF69B4").encode(
        x="Year",
        y="EBITDA",
        tooltip=["Year", "EBITDA"]
    ).properties(
        title="EBITDA Trend",
        width=600,
        height=300
    )
    
    # Calculate risk score
    ebitda = company_data.get('EBITDA', 0)
    ebitda_margin = company_data.get('EBITDA Margin', 0)
    interest_coverage = company_data.get('Interest Coverage', 0)
    leverage_ratio = company_data.get('Leverage Ratio', 0)
    
    if ebitda <= 0:
        ebitda_factor = 20  # Maximum risk for negative EBITDA
    else:
        # Calculate EBITDA margin component - cap between 0-20
        ebitda_factor = max(0, min(20, 20 * (1 - ebitda_margin)))
    
    # Handle negative or zero Interest Coverage
    if interest_coverage <= 0:
        coverage_factor = 40  # Maximum risk for negative coverage
    else:
        # Calculate coverage component - cap between 0-40
        coverage = min(interest_coverage, 10)  # Cap at 10x
        coverage_factor = max(0, min(40, 40 * (1 - coverage/10)))
    
    # Handle negative Leverage Ratio
    if leverage_ratio < 0:
        leverage_factor = 20  # Medium risk for negative leverage (could be good or bad)
    else:
        # Calculate leverage component - cap between 0-40
        leverage = min(leverage_ratio, 8)  # Cap at 8x
        leverage_factor = max(0, min(40, 5 * leverage))
    
    # Sum all components to get final score
    risk_score = ebitda_factor + coverage_factor + leverage_factor
    
    # Ensure score is between 0-100
    risk_score = max(0, min(100, risk_score))
    
    return pn.Column(
        pn.pane.Markdown("## Performance Trends"),
        pn.pane.Vega(revenue_chart),
        pn.pane.Vega(ebitda_chart),
        pn.pane.Markdown("### Risk Score"),
        pn.pane.Markdown(f"Risk Score: {risk_score:.2f} (Lower is better; scale 0-100)")
    )

# Portfolio Comparison Section
metrics_selector = pn.widgets.MultiChoice(
    name="Select Metrics to Compare",
    options=["Revenue", "EBITDA", "Leverage Ratio", "Interest Coverage", "EBITDA Margin"],
    value=["Leverage Ratio", "Interest Coverage"]
)

def create_portfolio_comparison(filtered_df, metrics_to_compare):
    if filtered_df is None or filtered_df.empty or not metrics_to_compare:
        return pn.pane.Markdown("No data available for comparison.")
    
    # Format the displayed data for better readability
    display_df = filtered_df[["Company"] + metrics_to_compare].copy()
    
    # Format numerical columns based on their type
    for col in metrics_to_compare:
        if col in ["Revenue", "EBITDA"]:
            # Format large currency values
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
        elif col == "EBITDA Margin":
            # Format percentages
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}")
        else:
            # Format ratios to 2 decimal places
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}")
    
    return pn.widgets.DataFrame(display_df, name="Portfolio Comparison")

# Metric Comparison Visualization
def create_metric_visualization(filtered_df, selected_metrics, company):
    if filtered_df is None or filtered_df.empty or not selected_metrics:
        return pn.pane.Markdown("No data available for visualization.")
    
    # Filter to selected company if one is chosen
    if company:
        chart_data = filtered_df[filtered_df["Company"] == company].copy()
    else:
        chart_data = filtered_df.copy()
    
    if chart_data.empty:
        return pn.pane.Markdown("No data available for the selected filters.")
    
    # Create normalized data for visualization
    normalized_data = []
    
    for _, company_row in chart_data.iterrows():
        company_name = company_row["Company"]
        
        for metric in selected_metrics:
            try:
                value = float(company_row[metric])
                
                # Handle special cases for proper normalization
                if metric == "EBITDA Margin":
                    # Higher is better for margins, normalize to 0-1 (assuming margin between -100% and 100%)
                    normalized_value = (value + 1) / 2 if value < 0 else value
                elif metric == "Interest Coverage":
                    # Higher is better for coverage, cap at 20 for normalization
                    normalized_value = min(max(value, 0), 20) / 20
                elif metric == "Leverage Ratio":
                    # Lower is better for leverage, cap at 10 for normalization
                    # Invert so higher values = better (for consistent color scheme)
                    normalized_value = 1 - (min(max(value, 0), 10) / 10)
                elif metric in ["Revenue", "EBITDA"]:
                    # For revenue/EBITDA, normalize relative to the dataset
                    all_values = filtered_df[metric].astype(float)
                    min_val, max_val = all_values.min(), all_values.max()
                    # For negative EBITDA, treat worse than zero
                    if metric == "EBITDA" and value < 0:
                        norm_val = value / min_val if min_val < 0 else 0
                        normalized_value = 0.5 * (1 + norm_val)  # Scale to 0-0.5 range
                    else:
                        # Regular normalization for positive values
                        range_val = max_val - min_val
                        normalized_value = (value - min_val) / range_val if range_val > 0 else 0.5
                else:
                    # Generic normalization (min-max scaling)
                    all_values = filtered_df[metric].astype(float)
                    min_val, max_val = all_values.min(), all_values.max()
                    range_val = max_val - min_val
                    normalized_value = (value - min_val) / range_val if range_val > 0 else 0.5
                
                # For visualization purposes, ensure values are in 0-1 range
                normalized_value = max(0, min(normalized_value, 1))
                
                normalized_data.append({
                    "Company": company_name,
                    "Metric": metric,
                    "Original_Value": value,
                    "Normalized_Value": normalized_value
                })
            except (ValueError, TypeError):
                # Skip if value can't be converted to float
                pass
    
    if not normalized_data:
        return pn.pane.Markdown("No valid data available for visualization.")
    
    # Create DataFrame from normalized data
    norm_df = pd.DataFrame(normalized_data)
    
    # Create a multi-series bar chart
    chart_height = max(300, len(chart_data) * 50)
    
    bar_chart = alt.Chart(norm_df).mark_bar().encode(
        x=alt.X("Normalized_Value:Q", title="Normalized Value (0-1)"),
        y=alt.Y("Company:N", title="Company"),
        color=alt.Color("Metric:N", 
                       scale=alt.Scale(scheme="category10"),
                       legend=alt.Legend(title="Metrics")),
        tooltip=["Company", "Metric", "Original_Value:Q", "Normalized_Value:Q"]
    ).properties(
        width=600,
        height=chart_height
    )
    
    # Return the visualization
    return pn.Column(
        pn.pane.Markdown("## Metric Comparison Visualization"),
        pn.pane.Markdown("### Metric Performance by Company"),
        pn.pane.Vega(bar_chart)
    )

# Create widgets with proper reactive dependencies
company_details_pane = pn.bind(create_company_details, company_data)
scenario_analysis_pane = pn.bind(create_scenario_analysis, company_data)
performance_trends_pane = pn.bind(create_performance_trends, company_data)
portfolio_comparison_pane = pn.bind(create_portfolio_comparison, filtered_df_panel, metrics_selector)
metric_visualization_pane = pn.bind(create_metric_visualization, filtered_df_panel, metrics_selector, company_selector)

# Assemble the Dashboard
overview_pane = create_overview_chart()

# Create tabs for organized viewing
tabs = pn.Tabs(
    ("Overview", pn.Row(
        pn.Column(
            overview_pane,
            pn.pane.Markdown("### Filters"),
            category_filter,
            sector_filter
        )
    )),
    ("Company Details", pn.Row(
        pn.Column(
            company_selector,
            company_details_pane
        )
    )),
    ("Scenario Analysis", scenario_analysis_pane),
    ("Performance Trends", performance_trends_pane),
    ("Portfolio Comparison", pn.Column(
        pn.pane.Markdown("## Portfolio Comparison"),
        metrics_selector,
        portfolio_comparison_pane
    )),
    ("Visualizations", metric_visualization_pane)
)

# Main Layout
dashboard = pn.Column(
    pn.pane.Markdown("# Private Credit Portfolio Monitoring Dashboard"),
    pn.pane.Markdown("Interactive dashboard to monitor a hypothetical direct lending portfolio of 9 companies."),
    tabs
)

# Create and serve the dashboard
dashboard.servable()
