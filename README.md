# طريقة نشر الفتنة بين المسلمين باستخدام الهندسة العكسية
First of all, I intended to write this article in Arabic, but Obsidian MD gets weird with Right-to-Left languages and I'm used to the software فتباً للغرب.

So, after I caught your attention with the catchy title, let's learn about game hacking :')

## Backstory 
Do you know when you make a quick decision about what you'll do for the week and then end up staring at a debugger at 2 a.m. in the morning wondering why the program didn't take the jump you based your whole static analysis on?
Yeah, welcome to **Game Hacking®™©.**

I chose to play with *Stronghold Crusader* cause it's old enough not to be complex, fun, and most importantly because it has the one and only ***Saladin ibn Ayyub*** (معا لاحياء الدولة الايوبية). 

**Warning**: some of the conclusions I'll get to may appear to be arbitrary, that's because A LOT was the result of ***trial and error***! I basically *wanted answers, not explanations*. 

## The idea and the execution
The idea is simple, make the army turn on each other. 
How can we achieve that? Well, the only case the army would attack is if it engages with an enemy, so we'll need to somehow make the soldiers enemies.

Now we'll lay some hypotheses about how we might achieve that:

![](./Attachments/Pasted%20image%2020210506013248.png)
- First of all, we can assume that the army's soldiers are **stored in an *array***.
- Every element in the array will have **the info/description** of a soldier aka the soldier's **health**, **type** (a *Horse Archer*, or an *Arabian Bow*, etc...) 
- alliance

## Game mechanics
Before we continue, we need to understand how the game is played to form a little sense for what will come:
- How to build an army?
	- You recruit/train a *Peasant* (a citizen in the game) to become a soldier. We'll call it "buying a soldier" from now on.
	- There are several types of soldiers in the game. 
	- The army's size depends on the Peasants' count and the amount of gold you have.
	- If you have 1 billion gold and 0 Peasants you can't train/buy a soldier.
- How can we get more *Peasants* 
	- The *Peasants*' count **increases linearly** over time as long as you have enough houses


## Walkthrough
#### Missing around
The first thing I did was playing with Cheat Engine (a memory scanner) to see what I can change and what interesting addresses I can find.

![](./Attachments/Pasted%20image%2020210506014153.png)

A while later, I found an address that stores the total number of soldiers I have bought. That means the code that writes to this address is ***the code that handles buying soldiers.*** Off to a good start!

![](./Attachments/Pasted%20image%2020210506014316.png)

So I noted the address of the instruction and jumped right into Ghidra -a top-notch troja.. I mean disassembler made by the NSA- to see what happens around that address. 

![](./Attachments/Pasted%20image%2020210506014911.png)

Then I got this error.  

![](./Attachments/Pasted%20image%2020210506015016.png)

It was solved by unchecking the "Create Export Symbol Files" option (idk why).

Now to the function.

#### Static analysis

![](./Attachments/Pasted%20image%2020210506015409.png)

And oh god make it stop my eyes are bleeding :')

Keep in mind that this function is related to buying soldiers.
The first thing to notice in the function is the chain of if statements:

![](./Attachments/Pasted%20image%2020210507141748.png)

It sets the value of `iVar3`, then subtracts it from an address:

![](./Attachments/Pasted%20image%2020210507140235.png)

You'll notice that the values assigned to `iVar3` is similar to **the prices of different types of units** in the game. So it's safe to assume the if statements check the type of the soldier, `iVar3` is the soldier's price, and the address is the gold.

Before I continued diving into the function I needed to know a little bit more about its parameters.

![](./Attachments/Pasted%20image%2020210506021938.png)

![](./Attachments/Pasted%20image%2020210506022000.png)

I noticed that in the decompiler there were **5 parameters**, the first one having a weird name. In the disassembler,** there were only 4 parameters**. At first, I thought Ghidra was on Ketamine, then I noticed the `__thiscall`. Turns out this is a [C++ calling convention](https://docs.microsoft.com/en-us/cpp/cpp/thiscall?view=msvc-160). This function belongs to a class and `param_1_00` was `this` and it's being passed via the register `ecx`.

Now is a good time for debugging :)

#### Debugging
Ok, we know that the first parameter is the unit type, what now?
As I was reversing I noticed that the game had stopped on a breakpoint I set earlier on this function (on its own). I didn't buy any soldiers so I continued the debugger and waited. The game hit the breakpoint again. That means the computer opponent also uses this function to buy soldiers! 

New hypothesis:
- The array of entities also includes the opponent's entities. 

I then compared the stack on my call and the opponent's call:

![](./Attachments/Pasted%20image%2020210506023833.png)(My call)

![](./Attachments/Pasted%20image%2020210506024835.png)(Opponent's call)

I found out that *parameter 3 was the player's id*. That's big, it confirms our hypothesis that troops have the *alliance* property. So if we managed to change it, soldiers will become enemies.

Now we need to continue debugging until we find where the location of that array is.

Eventually, you'll get to this block:

![](./Attachments/Pasted%20image%2020210506033751.png)

It compares whatever is in `ecx` to one, if it's less than or equal, it exits. 
I played a little with the address at `ecx`, it ***increases linearly*** on its own.

New hypothesis:
- `ecx` holds the length of the entities array

The next code block is a loop with a series of checks:

![](./Attachments/Pasted%20image%2020210506035721.png)

Can I tell you a secret? 
I didn't continue reversing this function because I found the answers I wanted in the checks!

There is an interesting condition here:
- `cmp esi, dword ptr ds:[ecx]; jl`

Since `esi` is the counter and is being compared to `[ecx]` (**entities count**). This might mean that the loop checks for available entities/*Peasants* to be soldiers. For example, a *Peasant* with no job is available to be a soldier, but another soldier can't be.

That means this is a **loop over the entities array**!

- The instruction (`lea edx, dword ptr ds:[ecx+D64]`) gets executed before the loop, 
- then during the loop, `edx` is referenced.
- At the end of the loop 1 is added to the counter `esp` and `0x490` is added to `edx`. 

As the code hints:
- `ecx+D64` is the address of the entities' array. 
- Each entity has a size of `0x490` bytes.

I played with the soldier structure in memory for a while and I found that:
- `edx+25e` holds the *type byte*.
	- Found it by buying a big amount of `0x4a` type units.
- `edx+266` holds the *alliance byte*! 
	- Since the human player's id is `1`, I found it by changing the `1`'s closer to the *type byte* to `2`'s and noticing the game's behavior.
  
Now that we can change the alliance, let's automate that!

#### Automation
I chose Python to write the hack, and I swear to god if hear one more bad comment about Python for game hacks I'll show up when you're asleep >:(

The script's goal is to read the memory to get the entities count, loop over the entities array, then go to the offset `0x266` to change the alliance.

For reading/writing to memory, we'll use `pymem`. We'll also use `pywin32` to access Windows API to get the game's PID for it to be used by `pymem`. 

While running the script I noticed that the *Warlords* (the human player & the opponent) could change their alliance, turns out they're also in the entities array with the type `55` or `0x37` so I made an exception for them in the script. 

## The results
Before:
![](./Attachments/Pasted%20image%2020210507173724.png)

After:
![](./Attachments/Pasted%20image%2020210507174020.png)
