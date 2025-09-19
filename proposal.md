# NaturalDB - A Natural-Language-Driven NoSQL Database System and its Application in E-commerce
Course Project of DSCI 551: Data Management

Option: **NoSQL Database System**

Dataset (provisional): [Amazon Sales Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset)

## Overview
This project proposes the design and implementation of **NaturalDB**, a NoSQL database system capable of storing and querying JSON data while supporting natural language queries.

The system will provide:

- CRUD operations (Create, Read, Update, Delete).

- Advanced query functions such as filtering, projection, group-by, aggregation, and join.

- A lightweight storage backend designed to efficiently store and retrieve JSON data.

- A query engine to parse and execute structured queries.

- An LLM-powered natural language interface that translates user queries into executable operations.

- A security layer to protect sensitive operations (update/delete) through authorization or confirmation.

To showcase NaturalDB, the [Amazon Sales Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset) will be preprocessed into JSON-based collections (e.g., Products, Ratings, Customers). A simple e-commerce application will be developed as a demonstration, allowing users to browse products, view ratings, and manage orders via natural language interaction.

## Project Architecture
Here is a bottom-up architecture of the proposed system:
![architecture](architecture.png)
### Layer 1: Storage System
In this layer, we are going to find a pattern to store JSON data efficiently. A naive idea is to use a file-based key-value store, where the key is the unique identifier of each JSON object, and the value is the JSON object itself. We use folders to map tables (e.g. `Products/` <-> `Products` table), and use files to map records (e.g. `Products/1.json` <-> `Products` table's record with id 1).

Due to limited time, we may not implement advanced techniques like indexing, sharding, or replication. Transactions may be minimally supported by **locking files** during write operations to ensure data consistency.

### Layer 2: JSON Parser and Query Engine
In this layer, we are going to implement a JSON parser and a query engine. The JSON parser is responsible for parsing JSON data from files and converting them into a Python object (e.g. dictionary, array), working as `json.load()` but not relying on libraries like `json`.

The query engine is responsible for executing queries on the JSON data, implementing functions for **filtering, projection, group by, aggregation**, and **join**.

### Layer 3: LLM-powered Natural Language Query Interface
In this layer, we are going to implement an LLM-powered NLP module that can convert natural language queries into the query functions supported by our query engine (e.g. "Find orders with rating 5" -> `orders.filter(rating=5)`). To ensure security, we *may* restrict sensitive operations like update and delete to authorized users only, or require confirmation from developers when executing such operations (like a `force=True` flag).

We will use **Python Flask** to build a RESTful API for our database system, allowing the front-end application to interact with the database using HTTP requests using natural language queries. If time permits, we will publish this application as a **Python package** for easy installation and usage.

We may use some LLM services (e.g. OpenAI GPT-5, Google Gemini) to help us with the NLP tasks by prompt engineering like providing some examples of natural language queries and their corresponding query functions. If they do not work well, we may introduce advanced LLM techniques such as fine-tuning, MCP, or functional calls.

### Layer 4: E-commerce Front-end Application (...or whatever!)
In this layer, we are going to build a simple E-commerce front-end application using **Next.js**. The application will allow users to browse products, view ratings, and manage their orders on top of the database system, by accepting natural language queries from users and calling the Flask back-end API to interact with the database system. (In fact, this layer can be anything. The E-commerce application is just an example.)

## Deployment
For both the back-end and front-end applications, we will use **Vercel** for deployment, as it provides a simple and efficient way to deploy web applications. We will set up CI/CD pipelines to automate the deployment process.

## Timeline
| Week # | Start Date (Monday) | Task                                      |
|------|----------------------|-------------------------------------------|
| 3    | 2025-09-15           | Project proposal submission               |
| 4    | 2025-09-22           | Dataset collection and preprocessing; GitHub repository setup       |
| 5    | 2025-09-29           | Implement Layer 1: Storage System (design classes to handle operation on JSON files and folders)       |
| 6    | 2025-10-06           | Implement Layer 2 (part 1): JSON Parser (implement functions to parse JSON data from files) and simple query functions       |
| 7    | 2025-10-13           | Implement Layer 2 (part 2): Query Engine (implement complex functions for filtering, projection, group by, aggregation, and join)       |
|| **2025-10-17** | **Midterm Evaluation** |
| 8    | 2025-10-20           | Implement Layer 3: LLM-powered Natural Language Query Interface (create Flask back-end APIs that rely on LLM services to translate queries and call functions)       |
| 9    | 2025-10-27           | Implement Layer 4: E-commerce Front-end Application (build a simple front-end application using Next.js)       |
| 10   | 2025-11-03           | Integration and Testing (integrate all layers and test the system)       |
| 11   | 2025-11-10           | Deployment (deploy the back-end and front-end applications using Vercel)       |
| 12   | 2025-11-17           | Final Testing and Documentation (final testing and write project report and documentation)       |
| | **2025-11-23** | **Project Report Submission**       |
| | **2025-11-24** | **Project Demo** |

Milestones:
- Week 5: Complete Layer 1: Storage System
- Week 7 (Before Midterm Report): Complete Layer 2: JSON Parser and Query Engine
- Week 8: Complete Layer 3: LLM-powered Natural Language Query Interface
- Week 10: Complete Layer 4: E-commerce Front-end Application