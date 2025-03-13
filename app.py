import streamlit as st
import os
import json
import requests
import base64
from datetime import datetime, timedelta
import anthropic
import pandas as pd
from dotenv import load_dotenv
import re
import random

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Content Recommendation Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
        background: linear-gradient(90deg, #1E88E5, #5E35B1);
        color: white;
        padding: 10px;
        border-radius: 10px;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        font-weight: 600;
        text-align: center;
        margin-bottom: 20px;
    }
    .platform-button {
        padding: 20px 10px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
        cursor: pointer;
        margin: 5px;
        transition: transform 0.2s;
        border: none;
    }
    .platform-button:hover {
        transform: scale(1.05);
    }
    .linkedin-button {
        background-color: #0077B5;
    }
    .x-button {
        background-color: #1DA1F2;
    }
    .tiktok-button {
        background-color: #000000;
    }
    .platform-selected {
        border: 4px solid #FFD700;
        transform: scale(1.05);
    }
    .big-button {
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
        text-align: center;
        margin: 20px 0;
        cursor: pointer;
        border: none;
        transition: background-color 0.3s;
    }
    .big-button:hover {
        background-color: #45a049;
    }
    .auto-button {
        padding: 20px;
        font-size: 24px;
        font-weight: bold;
        border-radius: 15px;
        background: linear-gradient(45deg, #FF5722, #FF9800);
        color: white;
        text-align: center;
        margin: 20px 0;
        cursor: pointer;
        border: none;
        transition: transform 0.3s;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .auto-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    .content-box {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    .highlight {
        background-color: #FFF176;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .stButton>button {
        width: 100%;
    }
    .search-result {
        margin-bottom: 15px;
        padding: 15px;
        border-radius: 10px;
        background-color: #f5f5f5;
        border-left: 6px solid #4CAF50;
    }
    .insight-box {
        padding: 15px;
        background-color: #E3F2FD;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #90CAF9;
    }
    .section-title {
        background-color: #3949AB;
        color: white;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        font-weight: bold;
        text-align: center;
    }
    .card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-top: 5px solid #3949AB;
        color: #333;
    }
    .step-number {
        display: inline-block;
        width: 30px;
        height: 30px;
        background-color: #3949AB;
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 30px;
        margin-right: 10px;
    }
    .step-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #3949AB;
    }
    .hint-text {
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
        margin-top: 5px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    .card p, .card li, .card h1, .card h2, .card h3, .card h4, .card h5, .card h6 {
        color: #333 !important;
    }
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #333;
    }
    [data-testid="stExpanderContent"] {
        color: #333 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        color: #333 !important;
        background-color: #ffffff;
    }
    .stTabContent {
        color: #333 !important;
    }
    .streamlit-expanderContent {
        color: #333 !important;
    }
    .element-container .stMarkdown {
        color: #333;
    }
    div.stTabs div[data-baseweb="tab-panel"] div.markdown-text-container p {
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# API Keys
EXA_API_KEY = os.getenv("EXA_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PROFILE_INFO = os.getenv("PROFILE_INFO")
PASSWORD = os.getenv("PASSWORD")

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # First run or password incorrect
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
        
    # Return True if the password is validated
    if st.session_state["password_correct"]:
        return True
    
    # Show input for password
    st.markdown("<h1 class='main-header'>Content Recommendation Agent</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>Password Protected</h2>", unsafe_allow_html=True)
    st.write("Please enter the password to access content recommendations.")
    
    # Create password input field
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Incorrect password. Please try again.")
    
    return False

# Initialize Anthropic client more safely
try:
    # First try with the standard initialization
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except TypeError as e:
    if "unexpected keyword argument 'proxies'" in str(e):
        # If the error is about proxies, try an alternative initialization
        # The error suggests the client is being initialized with proxies when it shouldn't
        import httpx
        from anthropic import Anthropic
        
        # Create a client without proxy configuration
        http_client = httpx.Client(
            base_url="https://api.anthropic.com",
            timeout=60.0,
            follow_redirects=True
        )
        
        try:
            # Try initializing with just the API key and http_client
            claude = Anthropic(api_key=ANTHROPIC_API_KEY, http_client=http_client)
        except Exception as inner_e:
            # If that still fails, try the most basic initialization
            claude = Anthropic(api_key=ANTHROPIC_API_KEY)
            st.warning(f"Using fallback Anthropic client initialization: {str(inner_e)}")
    else:
        # If it's some other error, re-raise it
        raise

# Load Raimond's profile from environment variables
def load_profile():
    try:
        if PROFILE_INFO:
            st.session_state.profile_loaded = True
            return PROFILE_INFO
        else:
            return "Profile information not found in environment variables. Please check your .env file."
    except Exception as e:
        return f"Error loading profile: {str(e)}"

# Enhanced Exa search function with more parameters and better error handling
def exa_search(query, num_results=5, days_back=7, search_depth="basic", highlight_query=None):
    url = "https://api.exa.ai/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": EXA_API_KEY
    }
    
    # Calculate the date for filtering results
    if days_back > 0:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    else:
        start_date = None
    
    payload = {
        "query": query,
        "num_results": num_results,
        "use_autoprompt": True,
        "include_domains": [],
        "exclude_domains": [],
        "text": True,
        "search_depth": search_depth,
        "start_published_date": start_date
    }
    
    try:
        with st.spinner(f"Searching for '{query}'..."):
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            results = response.json().get('results', [])
            
            # Process results to add additional information
            for result in results:
                # Extract publish date if available
                result['published_date'] = result.get('published_date', 'Unknown date')
                
                # Calculate reading time
                text = result.get('text', '')
                word_count = len(text.split())
                reading_time = max(1, round(word_count / 200))  # Assuming 200 words per minute
                result['reading_time'] = reading_time
                
                # Highlight search terms if provided
                if highlight_query:
                    terms = highlight_query.split()
                    highlighted_text = text
                    for term in terms:
                        if len(term) > 3:  # Only highlight terms with more than 3 characters
                            pattern = re.compile(r'\b{}\b'.format(re.escape(term)), re.IGNORECASE)
                            highlighted_text = pattern.sub(f'<span class="highlight">{term}</span>', highlighted_text)
                    result['highlighted_text'] = highlighted_text
                else:
                    result['highlighted_text'] = text
            
            return results
    except Exception as e:
        st.error(f"Exa search error: {str(e)}")
        return []

# Extract key insights from search results using Claude
def extract_insights(search_results, industry_terms, platform):
    if not search_results:
        return "No insights available. Please perform a search first."
    
    # Format search results for Claude
    formatted_results = "\n\n".join([
        f"Article: {result.get('title', 'No title')}\n"
        f"Source: {result.get('url', 'No URL')}\n"
        f"Date: {result.get('published_date', 'Unknown date')}\n"
        f"Summary: {result.get('text', 'No text')[:500]}..."
        for result in search_results[:5]  # Limit to first 5 results
    ])
    
    prompt = f"""Analyze these search results about {industry_terms} and extract 5-7 key insights that would be relevant for creating content on {platform}.

Search Results:
{formatted_results}

For each insight:
1. Provide a short headline/title
2. Briefly explain why this is relevant to the industry
3. Suggest how it could be used in content (specific angle or take)

Focus on identifying trends, newsworthy items, controversial topics, and opportunities for thought leadership in the {industry_terms} space.
"""
    
    try:
        response = claude.messages.create(
            model="claude-3-haiku-20240307",  # Using a faster model for analysis
            max_tokens=1000,
            temperature=0.3,
            system="You are an expert content researcher and trend analyst specializing in extracting valuable insights from news and articles for social media content creation.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error extracting insights: {str(e)}"

# Generate content using Claude with enhanced prompting
def generate_content(platform, profile_info, search_results, current_date, tone=None, content_type=None, specific_focus=None):
    # Prepare search results for Claude
    formatted_search_results = "\n\n".join([
        f"Title: {result.get('title', 'No title')}\n"
        f"Date: {result.get('published_date', 'Unknown date')}\n"
        f"URL: {result.get('url', 'No URL')}\n"
        f"Summary: {result.get('text', 'No text')[:300]}..."
        for result in search_results
    ])
    
    # Define customization options
    tones = {
        "professional": "Professional, thoughtful, and authoritative. Use industry terminology appropriately.",
        "conversational": "Friendly, approachable, and relatable. Like speaking to a colleague over coffee.",
        "thought_leadership": "Visionary, insightful, and forward-thinking. Position the author as an industry expert.",
        "educational": "Clear, informative, and helpful. Focus on teaching concepts and explaining ideas.",
        "storytelling": "Narrative-focused, engaging, and personal. Use anecdotes and examples."
    }
    
    content_types = {
        "news_commentary": "Commentary on current news/trends with the author's unique perspective.",
        "how_to": "Practical tips, advice, or step-by-step instructions on solving a problem.",
        "industry_insight": "Analysis of industry developments, challenges, or opportunities.",
        "success_story": "Share a success, case study, or positive outcome related to the author's work.",
        "question_engagement": "Pose a thoughtful question to encourage audience engagement and discussion."
    }
    
    platform_guidelines = {
        "X": {
            "format": "Short, concise posts (under 280 characters). Can include hashtags, mentions.",
            "best_practices": "Use threads for longer content. Include relevant hashtags (2-3 max). Consider adding one high-quality image.",
            "posting_frequency": "1-5 times per day, spaced out. Engagement with replies is important.",
            "optimal_times": "Early morning (7-9am), lunch (11am-1pm), and evening commute (5-7pm)."
        },
        "LinkedIn": {
            "format": "Professional tone, industry insights, longer-form content acceptable (1300-1500 characters ideal).",
            "best_practices": "Start with a hook. Use line breaks for readability. Include a call to action. Relevant hashtags (3-5).",
            "posting_frequency": "1-2 times per weekday, primarily during business hours.",
            "optimal_times": "Tuesday, Wednesday, Thursday between 8-10am or 1-2pm."
        },
        "TikTok": {
            "format": "Casual, entertaining, trend-aware content. Should be adaptable to short video format with hooks and calls to action.",
            "best_practices": "Script should have a strong hook in first 3 seconds. Clear value proposition. Conversational style.",
            "posting_frequency": "At least 1-3 times per day, consistent posting schedule recommended.",
            "optimal_times": "9am, 12pm, 3pm, 6pm, and 9pm. Weekends often perform well."
        }
    }
    
    # Apply customization if provided
    tone_guide = tones.get(tone, "Use a tone that matches the platform and content.")
    content_type_guide = content_types.get(content_type, "Choose an appropriate content type for the platform.")
    focus_guide = f"Pay special attention to {specific_focus}." if specific_focus else ""
    
    platform_info = platform_guidelines.get(platform, {})
    platform_format = platform_info.get("format", "")
    platform_best_practices = platform_info.get("best_practices", "")
    platform_posting_frequency = platform_info.get("posting_frequency", "")
    platform_optimal_times = platform_info.get("optimal_times", "")
    
    prompt = f"""You are a personal content strategist for Raimond Murakas. 
Today is {current_date}.
I need you to craft 3 different high-quality post options for {platform} based on Raimond's profile and current relevant news/trends.

Here is Raimond's biography:
{profile_info}

Here are some current news/trends that might be relevant:
{formatted_search_results}

PLATFORM GUIDELINES:
- Format: {platform_format}
- Best Practices: {platform_best_practices}
- Posting Frequency: {platform_posting_frequency}
- Optimal Times: {platform_optimal_times}

CONTENT CUSTOMIZATION:
- Tone: {tone_guide}
- Content Type: {content_type_guide}
- Special Focus: {focus_guide}

For each post option:
1. Title/Theme: Give the post a title or theme
2. Content: Provide the exact text for the post, formatted exactly as it would appear on {platform}
3. Strategic Thinking: Explain why this content would resonate with Raimond's audience
4. Optimal Timing: Suggest specific days/times for posting based on content type
5. Hashtags: Recommend relevant, strategic hashtags (appropriate number for the platform)
6. Engagement Prompt: Suggest 1-2 follow-up comments Raimond could add to boost engagement

Make each post distinct in approach and focus. The content should be authentic to Raimond's voice and immediately ready to post without further editing.
"""
    
    try:
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2500,
            temperature=0.7,
            system="You are an expert content strategist who specializes in creating personalized social media content for executives and entrepreneurs. You excel at crafting authentic, platform-optimized content that drives engagement and supports business goals.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating content: {str(e)}"

# Function to create downloadable content
def get_download_link(content, filename, link_text):
    """Generate a link to download content as a file"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #4CAF50; text-decoration: none; border-radius: 5px; text-align: center; cursor: pointer; margin: 10px 0;">{link_text}</a>'
    return href

# Function to format the search results for better display
def format_search_results(results, platform):
    if not results:
        return st.warning("No search results found. Try adjusting your search parameters.")
    
    st.success(f"Found {len(results)} relevant topics")
    
    for i, result in enumerate(results):
        with st.expander(f"📄 {i+1}. {result.get('title', 'No title')}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Source:** [{result.get('url', 'No URL')}]({result.get('url', 'No URL')})")
                st.markdown(f"**Published:** {result.get('published_date', 'Unknown date')}")
                st.markdown(f"**Reading time:** {result.get('reading_time', '?')} minute(s)")
            
            with col2:
                # Add a button to use this specific result for content generation
                if st.button(f"Use for content", key=f"focus_{i}"):
                    st.session_state.focused_result = result
                    st.session_state.focused_index = i
                    st.success(f"✅ Topic selected for generation!")
            
            # Show highlighted text if available, otherwise regular text
            text = result.get('highlighted_text', result.get('text', 'No text'))
            st.markdown(f"**Content:** {text}", unsafe_allow_html=True)

# Auto-Generate All button function - runs the entire process automatically
def auto_generate_all(industry_terms, platform, num_results, days_back, search_depth, tone, content_type, specific_focus):
    with st.spinner("🚀 Step 1: Finding relevant topics..."):
        # Use a platform-specific template for searching
        search_templates = {
            "LinkedIn": f"latest business trends in {industry_terms}",
            "X": f"trending topics in {industry_terms}",
            "TikTok": f"viral business content {industry_terms}"
        }
        search_query = search_templates.get(platform, f"latest news in {industry_terms}")
        
        # Perform the search
        search_results = exa_search(
            search_query, 
            num_results=num_results, 
            days_back=days_back,
            search_depth=search_depth,
            highlight_query=industry_terms
        )
        
        if not search_results:
            st.error("❌ No search results found. The automated process cannot continue.")
            return
        
        st.session_state.search_results = search_results
        st.session_state.search_query = search_query
    
    with st.spinner("🧠 Step 2: Extracting content insights..."):
        # Generate insights from search results
        insights = extract_insights(
            search_results,
            industry_terms,
            platform
        )
        st.session_state.insights = insights
    
    with st.spinner("✍️ Step 3: Creating personalized content..."):
        # Load profile information
        profile_info = load_profile()
        
        # Get current date
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        # Generate content
        content = generate_content(
            platform,
            profile_info,
            search_results,
            current_date,
            tone=tone,
            content_type=content_type,
            specific_focus=specific_focus
        )
        st.session_state.generated_content = content
    
    st.success("✅ All done! Your personalized content has been generated!")

# Main application - only show if password is correct
if check_password():
    # App title and description with custom styling
    st.markdown("<h1 class='main-header'>Social Media Content Generator</h1>", unsafe_allow_html=True)
    
    # Date information
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    st.markdown(f"<p style='text-align: center; margin-bottom: 30px;'>Today is {current_date}</p>", unsafe_allow_html=True)
    
    # Industry terms definition
    industry_terms = "AI procurement, supply chain technology, B2B SaaS, procurement automation"
    
    # Simple platform selection with visual buttons
    st.markdown("<div class='section-title'>STEP 1: Choose Your Platform</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        linkedin_class = "platform-button linkedin-button"
        if st.session_state.get("platform") == "LinkedIn":
            linkedin_class += " platform-selected"
        
        if st.button("LinkedIn", key="linkedin_btn", 
            help="Professional content for business networking"):
            st.session_state.platform = "LinkedIn"
    
    with col2:
        x_class = "platform-button x-button"
        if st.session_state.get("platform") == "X":
            x_class += " platform-selected"
            
        if st.button("X (Twitter)", key="x_btn",
            help="Short-form content for real-time conversations"):
            st.session_state.platform = "X"
    
    with col3:
        tiktok_class = "platform-button tiktok-button"
        if st.session_state.get("platform") == "TikTok":
            tiktok_class += " platform-selected"
            
        if st.button("TikTok", key="tiktok_btn",
            help="Video scripts for trending content"):
            st.session_state.platform = "TikTok"
    
    # Show current selection
    if "platform" not in st.session_state:
        st.session_state.platform = "LinkedIn"  # Default
    
    platform_colors = {
        "LinkedIn": "#0077B5",
        "X": "#1DA1F2",
        "TikTok": "#000000"
    }
    
    platform_color = platform_colors.get(st.session_state.platform, "#4CAF50")
    
    st.markdown(f"<div style='text-align: center; margin: 20px 0; padding: 10px; background-color: {platform_color}; color: white; border-radius: 10px; font-weight: bold;'>Selected: {st.session_state.platform}</div>", unsafe_allow_html=True)
    
    # SIMPLE CONTENT SETTINGS
    st.markdown("<div class='section-title'>STEP 2: Quick Settings</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        tone = st.selectbox(
            "Content Tone 🎭",
            options=["professional", "conversational", "thought_leadership", "educational", "storytelling"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
    
    with col2:
        content_type = st.selectbox(
            "Content Type 📝",
            options=["news_commentary", "how_to", "industry_insight", "success_story", "question_engagement"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
    
    specific_focus = st.text_input(
        "Specific Focus (Optional) 🎯",
        placeholder="e.g., AI innovation, supply chain efficiency",
    )
    
    with st.expander("Advanced Search Settings ⚙️"):
        col1, col2 = st.columns(2)
        
        with col1:
            num_results = st.slider(
                "Number of results", 
                min_value=3, 
                max_value=15, 
                value=5,
            )
            
            days_back = st.slider(
                "How recent? (days)", 
                min_value=1, 
                max_value=30, 
                value=7,
            )
        
        with col2:
            search_depth = st.radio(
                "Search depth",
                options=["basic", "advanced"],
                horizontal=True,
                help="Basic is faster, advanced is more thorough"
            )
    
    # AUTO-GENERATE BUTTON
    st.markdown("<div class='section-title'>STEP 3: Generate Content</div>", unsafe_allow_html=True)
    
    # Create a big, eye-catching button for one-click automation
    auto_generate_col1, auto_generate_col2, auto_generate_col3 = st.columns([1,2,1])
    
    with auto_generate_col2:
        auto_button = st.button(
            "🔮 AUTO-GENERATE EVERYTHING! 🔮",
            help="Click once to automatically search, analyze, and generate content",
            key="auto_generate_btn"
        )
        st.markdown("<p class='hint-text' style='text-align: center;'>Click once and let the AI do all the work!</p>", unsafe_allow_html=True)
    
    if auto_button:
        auto_generate_all(
            industry_terms, 
            st.session_state.platform, 
            num_results, 
            days_back, 
            search_depth,
            tone,
            content_type,
            specific_focus
        )
    
    # Create a tabbed interface for viewing the different components
    if hasattr(st.session_state, 'search_results') or hasattr(st.session_state, 'insights') or hasattr(st.session_state, 'generated_content'):
        st.markdown("<div class='section-title'>STEP 4: Review Your Results</div>", unsafe_allow_html=True)
        
        tabs = st.tabs(["✨ Final Content", "🔍 Search Results", "💡 Content Insights"])
        
        # Tab 1: Final generated content (most important, so it's first)
        with tabs[0]:
            if hasattr(st.session_state, 'generated_content'):
                st.markdown("### Your Generated Content")
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(st.session_state.generated_content)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Add download option
                filename = f"content_{st.session_state.platform}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                download_link = get_download_link(st.session_state.generated_content, filename, "📥 Download content as text file")
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.info("Content hasn't been generated yet. Use the AUTO-GENERATE button above to create content.")
        
        # Tab 2: Search results
        with tabs[1]:
            if hasattr(st.session_state, 'search_results'):
                st.markdown("### Search Results")
                format_search_results(st.session_state.search_results, st.session_state.platform)
            else:
                st.info("No search results available. Use the AUTO-GENERATE button to perform a search.")
        
        # Tab 3: Insights
        with tabs[2]:
            if hasattr(st.session_state, 'insights'):
                st.markdown("### Content Insights")
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(st.session_state.insights)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No insights available. Use the AUTO-GENERATE button to extract insights.")
    
    # Add some additional information in the sidebar
    with st.sidebar:
        st.markdown("<h3 style='text-align: center;'>About This Tool</h3>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            This content generator creates personalized social media posts for Raimond Murakas based on:
            <ul>
            <li>✅ Current trending topics</li>
            <li>✅ Industry-specific news</li>
            <li>✅ Professional profile</li>
            </ul>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown("<h3 style='text-align: center;'>Simple Instructions</h3>", unsafe_allow_html=True)
        st.markdown(
            """
            <ol>
            <li><strong>Choose platform</strong> - LinkedIn, X, or TikTok</li>
            <li><strong>Select settings</strong> - Tone and content type</li>
            <li><strong>Click AUTO-GENERATE</strong> - One button does it all!</li>
            <li><strong>Review & download</strong> - Your content is ready!</li>
            </ol>
            """, 
            unsafe_allow_html=True
        )
        
        # Add a tip
        st.markdown("<h3 style='text-align: center;'>Tip of the Day</h3>", unsafe_allow_html=True)
        tips = [
            "The best time to post on LinkedIn is Tuesday through Thursday between 8-10am",
            "Use hashtags strategically - 2-3 for X, 3-5 for LinkedIn",
            "Educational content performs well across all platforms",
            "Always include a call-to-action in your posts",
            "Consistency is key - regular posting builds audience engagement"
        ]
        random_tip = random.choice(tips)
        st.markdown(f"""
        <div style='background-color: #fffde7; padding: 15px; border-radius: 10px; border-left: 5px solid #ffd54f;'>
        💡 <strong>Tip:</strong> {random_tip}
        </div>
        """, unsafe_allow_html=True)
        
        # Add a reset button
        if st.button("🔄 Reset Everything", help="Clear all generated content and start fresh"):
            for key in list(st.session_state.keys()):
                if key not in ['password_correct', 'platform']:
                    del st.session_state[key]
            st.success("✅ All content has been reset!") 