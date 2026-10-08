package main

import (
	nc "agentinterface/nativecore"
	"encoding/json"
	"fmt"
	"os"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: ai-contract <program.json>")
		os.Exit(2)
	}
	b, e := os.ReadFile(os.Args[1])
	if e != nil {
		panic(e)
	}
	var p nc.Program
	if e = json.Unmarshal(b, &p); e != nil {
		panic(e)
	}
	if e = nc.ValidateProgram(p); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
	s, e := nc.EncodeC1(p)
	if e != nil {
		panic(e)
	}
	fmt.Println(s)
}
