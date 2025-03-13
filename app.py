import streamlit as st
import os
import json
import requests
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    st.title("Content Recommendation Agent")
    st.subheader("Password Protected")
    st.write("Please enter the password to access content recommendations.")
    
    # Create password input field
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Incorrect password. Please try again.")
    
    return False

# Initialize Anthropic client
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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

# Exa search function
def exa_search(query, num_results=5):
    url = "https://api.exa.ai/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": EXA_API_KEY
    }
    
    payload = {
        "query": query,
        "num_results": num_results,
        "use_autoprompt": True,
        "include_domains": [],
        "exclude_domains": [],
        "text": True,
        "search_depth": "basic"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['results']
    except Exception as e:
        st.error(f"Exa search error: {str(e)}")
        return []

# Generate content using Claude
def generate_content(platform, profile_info, search_results, current_date):
    # Prepare search results for Claude
    formatted_search_results = "\n\n".join([
        f"Title: {result.get('title', 'No title')}\n"
        f"URL: {result.get('url', 'No URL')}\n"
        f"Snippet: {result.get('text', 'No text')}"
        for result in search_results
    ])
    
    platform_guidelines = {
        "X": "Short, concise posts (under 280 characters). Can include hashtags, mentions. Good for quick updates, news sharing, and engaging questions.",
        "LinkedIn": "Professional tone, industry insights, longer-form content acceptable. Focus on business value, professional achievements, and thought leadership.",
        "TikTok": "Casual, entertaining, trend-aware content. Should be adaptable to short video format with hooks and calls to action."
    }
    
    prompt = f"""You are a personal content strategist for Raimond Murakas. 
Today is {current_date}.
I need you to craft 3 different post options for {platform} based on Raimond's profile and current relevant news/trends.

Here is Raimond's biography:
{profile_info}

Here are some current news/trends that might be relevant:
{formatted_search_results}

Platform guidelines for {platform}: {platform_guidelines.get(platform, "")}

For each post option:
1. Include a draft of the post content
2. Explain the strategic thinking behind the post
3. Suggest optimal timing for posting
4. Recommend relevant hashtags if applicable

Make the content authentic to Raimond's voice and relevant to his industry (AI-powered procurement, supply chain, entrepreneurship).
"""
    
    try:
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
            system="You are an expert content strategist who specializes in creating personalized social media content for executives and entrepreneurs.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating content: {str(e)}"

# Main application - only show if password is correct
if check_password():
    # App title and description
    st.title("Personalized Content Recommendation Agent")
    st.subheader("For Raimond Murakas, CEO of SourceSmart")
    
    # Date information
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    st.write(f"Today is {current_date}")
    
    # Platform selection
    platform = st.selectbox(
        "Select your social media platform:",
        ["LinkedIn", "X", "TikTok"]
    )
    
    # Load profile information
    profile_info = load_profile()
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Profile", "Relevant Topics", "Recommendations"])
    
    with tab1:
        st.subheader("Your Profile Information")
        st.write(profile_info)
    
    with tab2:
        st.subheader("Finding Relevant Topics")
        
        # Different search queries based on the platform and profile
        industry_terms = "AI procurement, supply chain technology, B2B SaaS, procurement automation"
        
        search_queries = {
            "LinkedIn": f"latest news {industry_terms} business trends",
            "X": f"trending topics {industry_terms} tech innovation",
            "TikTok": f"viral business content {industry_terms} entrepreneur tips"
        }
        
        search_query = search_queries.get(platform, f"latest news {industry_terms}")
        
        if st.button("Find Relevant Topics"):
            with st.spinner(f"Searching for relevant topics for {platform}..."):
                search_results = exa_search(search_query)
                
                if search_results:
                    st.success(f"Found {len(search_results)} relevant topics")
                    
                    for i, result in enumerate(search_results):
                        with st.expander(f"{i+1}. {result.get('title', 'No title')}"):
                            st.write(f"**Source:** {result.get('url', 'No URL')}")
                            st.write(f"**Content:** {result.get('text', 'No text')}")
                else:
                    st.error("No relevant topics found. Please try again.")
                    
                # Store search results in session state
                st.session_state.search_results = search_results
    
    with tab3:
        st.subheader("Content Recommendations")
        
        if st.button("Generate Recommendations"):
            # Check if search results exist in session state
            if not hasattr(st.session_state, 'search_results') or not st.session_state.search_results:
                st.warning("Please find relevant topics first")
            else:
                with st.spinner(f"Generating personalized {platform} content..."):
                    content = generate_content(
                        platform,
                        profile_info,
                        st.session_state.search_results,
                        current_date
                    )
                    st.markdown(content)
    
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
            2. **Find relevant topics** - Search the web for current news and trends
            3. **Generate recommendations** - Get personalized content ideas based on your profile and the latest topics
            """
        ) 