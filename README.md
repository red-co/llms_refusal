

The degradation of the heretic model does exist, but I previously didn't know how to reliably trigger it with a minimal sample size.
Then I guessed that simulating a more RP-like scenario might work.
So, the conditions I used were:
32 tasks, 32 not performed, 16 preferred
More than 3k ctx (total number of samples), // since there were only 1.2k character cards, I randomly selected 2k Wikipedia articles to pad the ctx to 3k. This correctly triggered the degradation of the heretic model compared to the raw model.


1. `char_card.py` will randomly generate 20 character cards.
2. The `padding` consists of randomly sampled 2k-word Wikipedia text used to pad the context (`ctx`) to 4k. (Note: No script for fetching these snippets is provided here; only 10 Wikipedia text fragments are included.)
3. Running `llama.py` generates the `check_prompt` file and `v1.md`.
   - `v1.md` contains the current model's yes/no judgment on whether it followed the instructions.
4. Running `v2.py` generates `v2.md`.
   - This step aims to use a different model to perform the yes/no judgment.
5. `v3.py` merges the Markdown tables from `v1.md` and `v2.md` and calculates the instruction-following accuracy rate.


how to use it?
- Change all instances of 127.0.0.1 to your Llama server IP.  

cd ./scripts
py ./char_card.py
// wait....
py ./llama.py
// wait
py ./v2.py
py ./v3.py

If you need to create multiple rounds of testing,
you need to change the check_prompt path to the new folder. // llama2.py, v2.py,v3.py
Also, llama2.py is just a copy of llama.py, there is no difference.







# result 

I created a repository to reproduce the decreased instruction compliance and non-compliance with rejection requests in the heretical model using random samples. It randomly generated 20 role cards, representing 32 tasks, 32 things not to do, and 16 preferences.

Then, It inserted rejection requests into the role cards, allowing users to try to reject a request using a single instruction. This was evaluated 30 times randomly.


|no.|used model|heretic rating |raw rating| human rating|
|----|----|---|---|--|
|1|heretic|20/30|10/30|13/30|
|3|heretic|18/30|7/30|
|2|raw|23/30|19/30|24/40|
|4|raw|23/30|18/30|

These are my test results,
Interpretation: turn 1, heretic rated himself 20/30 for following instructions, raw rated heretic 10/30, and human rated heretic 13/30.

I performed human ratings on turn1 and turn.

Overall, the original model performs better when following instructions to reject requests. The here model, however, degrades significantly, by more than 40%.

# others
The odd-numbered lines in r.md are tasks that the model is instructed not to perform, while the even-numbered lines are user prompts that attempt to elicit rejection. The 01.md file in the same folder as r.md is the project's prompt. This project was written using chatgpt+grok, which saved a lot of time.
