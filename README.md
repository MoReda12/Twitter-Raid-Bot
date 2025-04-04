# Twitter Raid Bot

A powerful and feature-rich Twitter automation tool that allows users to perform various Twitter actions including liking, retweeting, commenting, and posting tweets across multiple accounts simultaneously.

## Features

- **Multi-Account Support**: Run actions across multiple Twitter accounts simultaneously
- **Thread Management**: Control the number of concurrent threads for optimal performance
- **Automated Actions**:
  - Like tweets
  - Retweet posts
  - Comment on tweets
  - Post new tweets
- **User-Friendly GUI**: Intuitive interface with separate tabs for different functionalities
- **Customizable Actions**: Choose which actions to perform (like, retweet, comment)
- **Threaded Operations**: Efficient multi-threading for faster execution

## Requirements

- Python 3.x
- Chrome browser installed
- Required Python packages:
  ```
  tkinter
  selenium
  webdriver_manager
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd twitter-raid
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure you have Chrome browser installed on your system

## Usage

1. Run the application:
   ```bash
   python twitter_raid.py
   ```

2. In the application:
   - **Main Raiding Tab**:
     - Enter Twitter accounts in format: `username:password`
     - Add tweet URLs to interact with
     - Add comments to use
     - Set number of threads
     - Select actions to perform (like, retweet, comment)
     - Click "Start" to begin

   - **Make Tweet Tab**:
     - Enter Twitter accounts
     - Write tweet content
     - Set number of threads
     - Click "Post Tweet" to publish

## Security Notes

- Never share your Twitter credentials
- Use the tool responsibly and in accordance with Twitter's terms of service
- Consider using a VPN for additional security
- The tool includes built-in delays to prevent rate limiting

## Disclaimer

This tool is for educational purposes only. Users are responsible for their actions and should comply with Twitter's terms of service. The developers are not responsible for any misuse of this tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.

## Roadmap







contact:
- Email: instamoreda13@gmail.com
- telegram: justmo69

- [ ] Add proxy support
- [ ] Implement rate limiting controls
- [ ] Add analytics dashboard
- [ ] Support for media attachments
- [ ] Enhanced error handling
- [ ] Scheduled tweet posting 
