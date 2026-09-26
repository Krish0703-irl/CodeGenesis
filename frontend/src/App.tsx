import { useState } from "react";
import Editor from "@monaco-editor/react";

function App() {
  const [code, setCode] = useState("// Write or paste your C++ code here");
  const [message, setMessage] = useState("");

  async function testBackend() {
    const response = await fetch("http://127.0.0.1:8000/hello");
    const data = await response.json();

    setMessage(data.message);
  }

  return (
    <div className="home">
      <h1>CodeGenesis</h1>

      <p>From Finished Code to Understanding</p>

      <Editor
        height="500px"
        defaultLanguage="cpp"
        value={code}
        onChange={(value) => setCode(value || "")}
        theme="vs-dark"
      />

      <button onClick={testBackend}>
        Teach Me This
      </button>

      <p>{message}</p>
    </div>
  );
}

export default App;