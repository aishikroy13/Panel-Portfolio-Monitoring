import panel as pn
import pandas as pd
import numpy as np
import altair as alt
import holoviews as hv

# Enable Panel extensions for Altair and HoloViews
pn.extension('altair')
hv.extension('bokeh')

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
        pn.pane.Altair(bar_chart)
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
@pn.depends(category_filter, sector_filter)
def filter_data(category, sectors):
    if category == "All":
        filtered = df.copy()
    else:
        filtered = df[df["Category"] == category].copy()
    
    if "All" not in sectors and sectors:
        filtered = filtered[filtered["Sector"].isin(sectors)]
    
    return filtered

# Create company selector that updates when filters change
@pn.depends(filter_data)
def get_company_options(filtered_df):
    if filtered_df.empty:
        return []
    return list(filtered_df["Company"])

company_selector = pn.widgets.Select(
    name="Select a Company",
    options=pn.bind(get_company_options, filter_data)
)

# Get company data based on selection
@pn.depends(filter_data, company_selector)
def get_company_data(filtered_df, company):
    if filtered_df.empty or company is None:
        return None
    
    company_data = filtered_df[filtered_df["Company"] == company]
    if company_data.empty:
        return None
    
    return company_data.iloc[0]

# Company Details Section
@pn.depends(get_company_data)
def create_company_details(company_data):
    if company_data is None:
        return pn.pane.Markdown("No company selected or no companies match the filters.")
    
    category_color = colors.get(company_data["Category"], "#FFFFFF")
    
    financial_data = pn.GridBox(
        pn.pane.Markdown(f"**Revenue:** ${company_data['Revenue']:,.2f}"),
        pn.pane.Markdown(f"**EBITDA:** ${company_data['EBITDA']:,.2f}"),
        pn.pane.Markdown(f"**Total Debt:** ${company_data['Total Debt']:,.2f}"),
        pn.pane.Markdown(f"**Interest Expense:** ${company_data['Interest Expense']:,.2f}"),
        pn.pane.Markdown(f"**Cash Flow:** ${company_data['Cash Flow from Operations']:,.2f}"),
        pn.pane.Markdown(f"**Leverage Ratio:** {company_data['Leverage Ratio']:.2f}"),
        ncols=3
    )
    
    other_metrics = pn.Column(
        pn.pane.Markdown(f"**Interest Coverage:** {company_data['Interest Coverage']:.2f}"),
        pn.pane.Markdown(f"**EBITDA Margin:** {company_data['EBITDA Margin']:.2%}"),
        pn.pane.HTML(f"<p><strong>Category:</strong> <span style='color:{category_color}'>{company_data['Category']}</span></p>"),
        pn.pane.Markdown(f"**Qualitative Notes:** {qualitative_notes[company_data['Company']]}")
    )
    
    export_button = pn.widgets.Button(name="Export Company Data to CSV", button_type="primary")
    
    @pn.depends(export_button.param.clicks)
    def export_data(clicks):
        if clicks:
            filename = f"data/{company_data['Company']}_export.csv"
            pd.Series(company_data).to_frame().T.to_csv(filename, index=False)
            return pn.pane.Alert(f"Exported data for {company_data['Company']} to '{filename}'", alert_type="success")
        return None
    
    return pn.Column(
        pn.pane.Markdown(f"## {company_data['Company']} Financial Health"),
        financial_data,
        other_metrics,
        export_button,
        export_data
    )

# Scenario Analysis Section
@pn.depends(get_company_data)
def create_scenario_widgets(company_data):
    if company_data is None:
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
    
    @pn.depends(interest_rate_slider, revenue_decline_slider)
    def update_scenario(interest_rate_change, revenue_decline):
        # Calculate new interest expense and coverage
        new_interest_expense = company_data["Interest Expense"] * (1 + interest_rate_change / 100)
        new_coverage = company_data["EBITDA"] / new_interest_expense if new_interest_expense > 0 else float('inf')
        
        # Calculate new revenue, EBITDA, and leverage
        new_revenue = company_data["Revenue"] * (1 - revenue_decline / 100)
        new_ebitda = company_data["EBITDA"] * (1 - revenue_decline / 100)
        new_leverage = company_data["Total Debt"] / new_ebitda if new_ebitda != 0 else float('inf')
        
        return pn.Column(
            pn.pane.Markdown(f"New Interest Coverage with {interest_rate_change:.2f}% rate change: {new_coverage:.2f}"),
            pn.pane.Markdown(f"New Leverage Ratio with {revenue_decline:.1f}% revenue decline: {new_leverage:.2f}")
        )
    
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
        update_scenario,
        footnote
    )

# Performance Trends Section
@pn.depends(get_company_data)
def create_performance_trends(company_data):
    if company_data is None:
        return pn.pane.Markdown("Select a company to view performance trends.")
    
    years = ["2021", "2022", "2023"]
    
    # Generate trend data for selected company
    ebitda_value = abs(company_data["EBITDA"])
    ebitda_fluctuation = ebitda_value * 0.1 if ebitda_value > 0 else 1000000
    
    trend_data = pd.DataFrame({
        "Year": years,
        "Revenue": np.random.normal(company_data["Revenue"], abs(company_data["Revenue"] * 0.1), 3),
        "EBITDA": np.random.normal(company_data["EBITDA"], ebitda_fluctuation, 3),
        "Company": [company_data["Company"]] * 3
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
    if company_data["EBITDA"] <= 0:
        ebitda_factor = 20  # Maximum risk for negative EBITDA
    else:
        # Calculate EBITDA margin component - cap between 0-20
        margin = company_data["EBITDA Margin"]
        ebitda_factor = max(0, min(20, 20 * (1 - margin)))
    
    # Handle negative or zero Interest Coverage
    if company_data["Interest Coverage"] <= 0:
        coverage_factor = 40  # Maximum risk for negative coverage
    else:
        # Calculate coverage component - cap between 0-40
        coverage = min(company_data["Interest Coverage"], 10)  # Cap at 10x
        coverage_factor = max(0, min(40, 40 * (1 - coverage/10)))
    
    # Handle negative Leverage Ratio
    if company_data["Leverage Ratio"] < 0:
        leverage_factor = 20  # Medium risk for negative leverage (could be good or bad)
    else:
        # Calculate leverage component - cap between 0-40
        leverage = min(company_data["Leverage Ratio"], 8)  # Cap at 8x
        leverage_factor = max(0, min(40, 5 * leverage))
    
    # Sum all components to get final score
    risk_score = ebitda_factor + coverage_factor + leverage_factor
    
    # Ensure score is between 0-100
    risk_score = max(0, min(100, risk_score))
    
    return pn.Column(
        pn.pane.Markdown("## Performance Trends"),
        pn.pane.Altair(revenue_chart),
        pn.pane.Altair(ebitda_chart),
        pn.pane.Markdown("### Risk Score"),
        pn.pane.Markdown(f"Risk Score: {risk_score:.2f} (Lower is better; scale 0-100)")
    )

# Portfolio Comparison Section
metrics_selector = pn.widgets.MultiChoice(
    name="Select Metrics to Compare",
    options=["Revenue", "EBITDA", "Leverage Ratio", "Interest Coverage", "EBITDA Margin"],
    value=["Leverage Ratio", "Interest Coverage"]
)

@pn.depends(filter_data, metrics_selector)
def create_portfolio_comparison(filtered_df, metrics_to_compare):
    if filtered_df.empty or not metrics_to_compare:
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
@pn.depends(filter_data, metrics_selector, company_selector)
def create_metric_visualization(filtered_df, selected_metrics, company):
    if filtered_df.empty or not selected_metrics:
        return pn.pane.Markdown("No data available for visualization.")
    
    # Filter to selected company if one is chosen
    if company is not None:
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
        pn.pane.Altair(bar_chart)
    )

# Assemble the Dashboard
def create_dashboard():
    # Create tabs for organized viewing
    tabs = pn.Tabs(
        ("Overview", pn.Row(
            pn.Column(
                create_overview_chart(),
                pn.pane.Markdown("### Filters"),
                category_filter,
                sector_filter
            )
        )),
        ("Company Details", pn.Row(
            pn.Column(
                company_selector,
                create_company_details
            )
        )),
        ("Scenario Analysis", create_scenario_widgets),
        ("Performance Trends", create_performance_trends),
        ("Portfolio Comparison", pn.Column(
            pn.pane.Markdown("## Portfolio Comparison"),
            metrics_selector,
            create_portfolio_comparison
        )),
        ("Visualizations", create_metric_visualization)
    )
    
    # Main Layout
    return pn.Column(
        pn.pane.Markdown("# Private Credit Portfolio Monitoring Dashboard"),
        pn.pane.Markdown("Interactive dashboard to monitor a hypothetical direct lending portfolio of 9 companies."),
        tabs
    )

# Create and serve the dashboard
dashboard = create_dashboard()
dashboard.servable()

