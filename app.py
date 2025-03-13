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
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        font-weight: 600;
    }
    .platform-card {
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .linkedin-card {
        background-color: #0077B5;
        color: white;
    }
    .twitter-card {
        background-color: #1DA1F2;
        color: white;
    }
    .tiktok-card {
        background-color: #000000;
        color: white;
    }
    .content-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 10px;
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
        padding: 10px;
        border-radius: 5px;
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    .insight-box {
        padding: 10px;
        background-color: #E3F2FD;
        border-radius: 5px;
        margin-bottom: 10px;
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
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# Function to format the search results for better display
def format_search_results(results, platform):
    if not results:
        return st.warning("No search results found. Try adjusting your search parameters.")
    
    st.success(f"Found {len(results)} relevant topics")
    
    platform_colors = {
        "LinkedIn": "#0077B5",
        "X": "#1DA1F2",
        "TikTok": "#000000"
    }
    color = platform_colors.get(platform, "#4CAF50")
    
    for i, result in enumerate(results):
        with st.expander(f"{i+1}. {result.get('title', 'No title')}"):
            st.markdown(f"**Source:** [{result.get('url', 'No URL')}]({result.get('url', 'No URL')})")
            st.markdown(f"**Published:** {result.get('published_date', 'Unknown date')}")
            st.markdown(f"**Reading time:** {result.get('reading_time', '?')} minute(s)")
            
            # Show highlighted text if available, otherwise regular text
            text = result.get('highlighted_text', result.get('text', 'No text'))
            st.markdown(f"**Content:** {text}", unsafe_allow_html=True)
            
            # Add a button to use this specific result for content generation
            if st.button(f"Focus on this topic for generation", key=f"focus_{i}"):
                st.session_state.focused_result = result
                st.session_state.focused_index = i
                st.info(f"Content generation will focus on topic #{i+1}: {result.get('title', 'No title')}")

# Main application - only show if password is correct
if check_password():
    # App title and description with custom styling
    st.markdown("<h1 class='main-header'>Personalized Content Recommendation Agent</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>For Raimond Murakas, CEO of SourceSmart</h2>", unsafe_allow_html=True)
    
    # Date information
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    st.write(f"Today is {current_date}")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Content Parameters")
        
        # Platform selection with visual cards
        st.write("**Select your social media platform:**")
        platform_col1, platform_col2, platform_col3 = st.columns(3)
        
        with platform_col1:
            linkedin_selected = st.button("LinkedIn", key="linkedin_btn", 
                help="Professional content for business networking")
            if linkedin_selected:
                st.session_state.platform = "LinkedIn"
        
        with platform_col2:
            x_selected = st.button("X", key="x_btn",
                help="Short-form content for real-time conversations")
            if x_selected:
                st.session_state.platform = "X"
        
        with platform_col3:
            tiktok_selected = st.button("TikTok", key="tiktok_btn",
                help="Video scripts for trending content")
            if tiktok_selected:
                st.session_state.platform = "TikTok"
        
        # Show current selection
        if "platform" not in st.session_state:
            st.session_state.platform = "LinkedIn"  # Default
        
        st.markdown(f"**Currently selected:** {st.session_state.platform}")
        
        # Advanced content customization
        st.subheader("Content Customization")
        
        tone = st.selectbox(
            "Content Tone",
            options=["professional", "conversational", "thought_leadership", "educational", "storytelling"],
            format_func=lambda x: x.replace("_", " ").title(),
            help="The tone and voice of the generated content"
        )
        
        content_type = st.selectbox(
            "Content Type",
            options=["news_commentary", "how_to", "industry_insight", "success_story", "question_engagement"],
            format_func=lambda x: x.replace("_", " ").title(),
            help="The format and purpose of the content"
        )
        
        specific_focus = st.text_input(
            "Specific Focus (Optional)",
            placeholder="e.g., AI innovation, supply chain efficiency",
            help="A specific topic or angle to emphasize"
        )
        
        # Search parameters
        st.subheader("Search Parameters")
        
        num_results = st.slider(
            "Number of results", 
            min_value=3, 
            max_value=15, 
            value=5,
            help="How many search results to retrieve"
        )
        
        days_back = st.slider(
            "Days back", 
            min_value=1, 
            max_value=30, 
            value=7,
            help="How recent the search results should be"
        )
        
        search_depth = st.select_slider(
            "Search depth",
            options=["basic", "advanced"],
            value="basic",
            help="Basic is faster, advanced is more thorough"
        )
    
    with col2:
        # Display platform-specific tips
        platform_tips = {
            "LinkedIn": "Best for: Professional insights, industry news, company updates, thought leadership",
            "X": "Best for: Trending topics, quick updates, news commentary, conversations, polls",
            "TikTok": "Best for: Educational content, behind-the-scenes, trending challenges, day-in-the-life"
        }
        
        st.info(platform_tips.get(st.session_state.platform, "Select a platform for specific tips"))
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Relevant Topics", "Content Insights", "Recommendations"])
        
        with tab1:
            st.subheader("Your Profile Information")
            # Load profile information
            profile_info = load_profile()
            st.markdown(profile_info)
        
        with tab2:
            st.subheader("Finding Relevant Topics")
            
            # Different search queries based on the platform and profile
            industry_terms = "AI procurement, supply chain technology, B2B SaaS, procurement automation"
            
            # Create columns for search input
            search_col1, search_col2 = st.columns([3, 1])
            
            with search_col1:
                # Pre-defined search queries for each platform as templates
                search_templates = {
                    "LinkedIn": [
                        f"latest business trends in {industry_terms}",
                        f"innovation in {industry_terms}",
                        f"challenges facing {industry_terms}",
                        f"future of {industry_terms}",
                        f"leadership in {industry_terms}"
                    ],
                    "X": [
                        f"trending topics in {industry_terms}",
                        f"breaking news {industry_terms}",
                        f"tech innovation {industry_terms}",
                        f"debate about {industry_terms}",
                        f"stats and facts {industry_terms}"
                    ],
                    "TikTok": [
                        f"viral business content {industry_terms}",
                        f"entrepreneur tips {industry_terms}",
                        f"day in the life {industry_terms}",
                        f"behind the scenes {industry_terms}",
                        f"educational content {industry_terms}"
                    ]
                }
                
                # Get templates for selected platform
                platform_templates = search_templates.get(st.session_state.platform, search_templates["LinkedIn"])
                
                # Allow user to select a template or create custom query
                search_option = st.radio(
                    "Choose search method:",
                    options=["Use template", "Custom query"],
                    horizontal=True
                )
                
                if search_option == "Use template":
                    search_query = st.selectbox(
                        "Select a search template:",
                        options=platform_templates
                    )
                else:
                    search_query = st.text_input(
                        "Enter custom search query:",
                        placeholder=f"e.g., latest news in {industry_terms}",
                        value=platform_templates[0]
                    )
            
            with search_col2:
                search_button = st.button("Find Topics", use_container_width=True)
                if search_button:
                    search_results = exa_search(
                        search_query, 
                        num_results=num_results, 
                        days_back=days_back,
                        search_depth=search_depth,
                        highlight_query=industry_terms
                    )
                    st.session_state.search_results = search_results
                    st.session_state.search_query = search_query
            
            # Display search results if available
            if 'search_results' in st.session_state:
                format_search_results(st.session_state.search_results, st.session_state.platform)
        
        with tab3:
            st.subheader("Content Insights")
            
            if st.button("Generate Content Insights"):
                if not hasattr(st.session_state, 'search_results') or not st.session_state.search_results:
                    st.warning("Please find relevant topics first")
                else:
                    insights = extract_insights(
                        st.session_state.search_results,
                        industry_terms,
                        st.session_state.platform
                    )
                    st.session_state.insights = insights
            
            if hasattr(st.session_state, 'insights'):
                st.markdown(st.session_state.insights)
        
        with tab4:
            st.subheader("Content Recommendations")
            
            if st.button("Generate Content"):
                # Check if search results exist in session state
                if not hasattr(st.session_state, 'search_results') or not st.session_state.search_results:
                    st.warning("Please find relevant topics first")
                else:
                    with st.spinner(f"Generating personalized {st.session_state.platform} content..."):
                        # Use focused result if available
                        search_data = st.session_state.search_results
                        if hasattr(st.session_state, 'focused_result'):
                            search_data = [st.session_state.focused_result]
                            focused_title = st.session_state.focused_result.get('title', 'this topic')
                            st.info(f"Generating content focused on: {focused_title}")
                        
                        content = generate_content(
                            st.session_state.platform,
                            profile_info,
                            search_data,
                            current_date,
                            tone=tone,
                            content_type=content_type,
                            specific_focus=specific_focus
                        )
                        st.session_state.generated_content = content
            
            if hasattr(st.session_state, 'generated_content'):
                st.markdown(st.session_state.generated_content)
                
                # Add download option
                filename = f"content_{st.session_state.platform}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                download_link = get_download_link(st.session_state.generated_content, filename, "Download content as text file")
                st.markdown(download_link, unsafe_allow_html=True)
    
    # Add some additional information in the sidebar
    with st.sidebar:
        st.title("About")
        st.info(
            "This content recommendation agent uses Exa AI to find relevant news "
            "and trending topics, then leverages Claude from Anthropic to generate "
            "personalized content recommendations specifically tailored for Raimond Murakas "
            "and his role at SourceSmart."
        )
        
        st.subheader("How it works")
        st.markdown(
            """
            1. **Select your platform** - Choose between LinkedIn, X, or TikTok
            2. **Customize content parameters** - Set tone, type, and focus
            3. **Find relevant topics** - Search the web for current news and trends
            4. **Generate insights** - Extract key points from search results
            5. **Create content** - Get personalized content ideas ready to post
            """
        )
        
        # Add quick tips section
        st.subheader("Quick Tips")
        tips = [
            "Focus on one specific search result for more targeted content",
            "Try different tones to find what resonates with your audience",
            "Educational content performs well across all platforms",
            "Always customize hashtags based on current trending topics",
            "The best posting times vary by day of week and audience location"
        ]
        
        # Display a random tip
        random_tip = random.choice(tips)
        st.markdown(f"💡 **Tip:** {random_tip}")
        
        # Add a reset button
        if st.button("Reset Session"):
            for key in list(st.session_state.keys()):
                if key not in ['password_correct', 'platform']:
                    del st.session_state[key]
            st.success("Session data has been reset") 