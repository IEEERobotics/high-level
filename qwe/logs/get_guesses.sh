cat unittests.log* | grep -i "Guess pose" | cut -f 2 -d "(" | tr "," " " | tr "@" " " | tr "+" " " | tr ")" " " | awk '{print $1,$2,$3}' > guesses
