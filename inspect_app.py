import requests

url = 'https://taiwan-weather-map.vercel.app/_next/static/chunks/app/page-8d320d6a6a0a98e9.js'
text = requests.get(url).text
with open('page_snippet.txt', 'w', encoding='utf-8') as f:
    f.write(text[13000:18000])
print('Saved snippet')
