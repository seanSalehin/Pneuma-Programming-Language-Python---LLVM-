# 🌟 Pneuma Programming Language v2.8.1

[![License](https://img.shields.io/badge/license-Custom-blue.svg)](LICENSE)

Pneuma (πνεῦμα) is a modern, JIT-style compiled programming language designed for clarity, performance, and expressive syntax. Inspired by the ancient Greek concept of "breath" or "spirit," Pneuma brings life to your ideas through clean, type-safe code.

---

## Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Project Rules](#-project-rules)
- [Language Guide](#-language-guide)
- [Learning Resources](#-learning-resources)
- [License](#-license)

---

## ✨ Features

✅ Core Language Capabilities

✅ Static Typing with type inference support

✅ JIT-style Execution for optimal performance

✅ First-class Functions with parameters, return types, and function call

✅ Complete Control Flow (if/else, while, do-while, scan/for, continue, break)

✅ Modular Programming with file imports

✅ Boolean Logic including negation operator (!false)

✅ Prefix & Postfix increment/decrement operations (++, --, , -26 )

✅ String Manipulation with type safety

✅ Comparison operators: ==, <, >, <=, >=

✅ Arithmetic Operations (x = x * 2)

✅ Assignment Operations	(*=, +=, -=, /=, !=) => (x *= 2;)

---

## 🚀 Quick Start

1. Create a new folder for your project (e.g., Pneuma).
2. Open the folder in your IDE or your code editor.
3. Install Python 3.7+ and Anaconda (or Miniconda) if not already installed.
4. Open your terminal (or Anaconda Prompt) inside the project folder.
5. Create and activate a dedicated Conda environment:
     conda create --name Pneuma python=3.12
     conda install llvmlite
     conda activate Pneuma
6. Clone the Repository: git clone https://github.com/seanSalehin/Pneuma-Programming-Language.git
7. Place all your .pn files in the Test folder.
8. Edit main.pn to write your program.
9. To run, execute (from the root folder): python main.py

---

## ⚡ Project Rules

Entry Point: All programs must contain act main() => return_type as the starting point
File Organization: Place all .pn source files within the Test folder
File Extensions: Use .pn for all Pneuma source files

---

## 📚 Language Guide

| Construct                 | Syntax Example                          | Description                        
|---------------------------|-----------------------------------------|---------------------------------|
| Variable                  | `mark x: int = 10;`                     | Declare and initialize variable |
| Function                  | `act foo() => int { ... }`              | Function definition             |
| Print                     | `printf("Value: %i", x);`               | Formatted output                |
| If-Else                   | `if x == 5 { ... } else { ... }`        | Conditional branching           |
| While                     | `while x < 10 { ... }`                  | Conditional loop                |
| Do-While                  | `while x < 10 { ... }`                  | Loop with condition checked post|
| Scan (For Loop)           | `scan (mark i=0; i<5; i++) { ... }`     | Counter-controlled loop         |
| Import                    | `load "module.pn";`                     | File/module inclusion           |
| Assignment Operations     | `x *= 2; x += 10;`                      | Compound assignment             |
| Arithmetic Operations     | `x = x * 2; x = x + 1;`                 | Basic arithmetic                |
| Boolean Logic             | `!false; x != 10;`                      | Negation and logical comparisons|
| Comparison Operators      | `==, !=, <, >, <=, >=`                  | All comparison types            |
| Prefix/Postfix Operations | `x++; x--; --x;`                        | Increment/decrement             |
| Negative Numbers          | `x = -12;`                              | Negative literals               |
| String Manipulation       | `printf("test %s", str);`               | Type-safe string operations     |
| Continue/Break            | `continue; break;`                      | Loop control statements         |
| First-class Functions     | `act main(a:int, b:int) => int { ... }` | Functions as values             |
| Function Call	            | `add(2, 3); result = add(2, 3);`        |Calling a function               |

---

## 📖 Learning Resources

For detailed tutorials and code samples, please navigate to the Tutorials.txt file inside the Test folder. This file contains step-by-step guides and practical examples to help you get started and understand the implementation process.

---

## 📄 License

© 2024 Pneuma Language Project. All rights reserved.

This project does not have an open-source license. By default, all rights are reserved. Use, modification, and distribution of the source code are not permitted without explicit permission from the project maintainer.


**Pneuma – Where every line breathes intention.**  
Maintainer: Sean Salehin  
Documentation Version: 2.8.0  
Last Updated: December 2024
