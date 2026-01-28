# 1.Function for reverse words (insight from practice python)
def reverse_words(sentence: str) -> str:
    words = sentence.split()
    reversed_words = words[::-1]
    return " ".join(reversed_words)

print(reverse_words("hello world"))


# the actual way i understand how to write it confidently
text =("hello world")

sentence1=text.split(" ") # split the words turning them to a list
print(sentence1) #['hello', 'world']

sentence1=sentence1[-1::-1] # reverse the list order
print(sentence1) # ['world', 'hello']

result1=' '.join(sentence1)
print(result1)


# 2. Count vowels task in a function way
def count_vowels(text: str) -> int:
    vowels = "aeiou"
    count = 0

    for char in text.lower():
        if char in vowels:
            count += 1

    return count
text = input("Enter text: ")

print("Function vowel count:", count_vowels(text))



# The other way i learnt it and understand it in a non function way
text = input("Eneter your vowel: ")
print(text)

vowels = "aeiouAEIOU"
count = 0

for c in text: 
    if c in vowels:
        count +=1 # incrementing the value of the count b +1 for every vowel
print(count)

# FizzBuzz challenge with function
def fizzbuzz(n: int) -> None:
    for i in range(1, n + 1):
        if i % 3 == 0 and i % 5 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)

number = int(input("Enter a number: "))
print("Function version:")
fizzbuzz(number)




# FizzBuzz challenge without function
for i in range(1,100):
    if i%3 == 0 and i%5 == 0:
        print("FizzBuzz")
    elif i%5 == 0: 
        print("Buzz")
    elif  i%3 == 0:
        print("Fizz")
    else:
        print(i)









