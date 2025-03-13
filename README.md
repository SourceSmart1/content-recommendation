# Content Recommendation Agent

A personalized content recommendation system for Raimond Murakas, CEO of SourceSmart, that suggests social media posts based on his profile and current trending topics.

## Features

- **Platform Selection**: Generate content for LinkedIn, X (Twitter), or TikTok
- **Real-time Web Search**: Uses Exa AI to find relevant news and trending topics
- **AI-Generated Content**: Leverages Anthropic's Claude to craft personalized content recommendations
- **User-friendly Interface**: Built with Streamlit for easy navigation and use
- **Privacy-focused**: Stores sensitive profile information in the .env file, not in code

## Setup

1. Clone this repository
   ```
   git clone https://github.com/yourusername/content-recommendation.git
   cd content-recommendation
   ```

2. Install the required dependencies
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables
   Create a `.env` file in the root directory with the following:
   ```
   EXA_API_KEY=your_exa_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   PROFILE_INFO="your_multiline_profile_information"
   ```
   
   Note: The PROFILE_INFO variable contains the full biographical information for Raimond Murakas.
   This is stored in the .env file for privacy and security reasons, rather than in the code itself.

4. Run the Streamlit application
   ```
   streamlit run content_recommender.py
   ```

## How It Works

1. **Select a platform**: Choose between LinkedIn, X, or TikTok for your content
2. **Find relevant topics**: The app searches the web for the latest news and trends related to AI procurement, supply chain technology, and entrepreneurship
3. **Generate recommendations**: Get personalized content ideas based on Raimond's profile and the latest topics

## Privacy Considerations

- **Sensitive Information**: All personal information is stored in the .env file, which should not be committed to version control
- **Environment Variables**: The .env file is automatically loaded by the application but kept private
- **Profile Data**: Biographical information is loaded directly from environment variables rather than from source code files

## Technologies Used

- **Streamlit**: For the web interface
- **Exa AI**: For semantic search capabilities
- **Anthropic Claude**: For AI-powered content generation
- **Python**: Core programming language
- **python-dotenv**: For secure loading of environment variables

## License

MIT
