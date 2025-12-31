#!/usr/bin/env python3
"""
ANALYTICA DSL - Command Line Interface
======================================

Usage:
    analytica run <pipeline>              Run DSL pipeline string
    analytica exec <file.pipe>            Execute pipeline from file
    analytica validate <file.pipe>        Validate pipeline syntax
    analytica list-atoms                  List available atoms
    analytica build                       Interactive pipeline builder
    analytica serve                       Start API server

Examples:
    # Run inline pipeline
    analytica run 'data.load("sales.csv") | metrics.sum("amount")'
    
    # Execute from file
    analytica exec monthly_report.pipe --var year=2024 --var format=pdf
    
    # With JSON input
    echo '{"sales": 1000}' | analytica run 'data.from_input() | metrics.calculate(["sum"])'
    
    # Output as JSON
    analytica run 'data.load("test") | transform.filter(year=2024)' --output json
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsl.core.parser import (
    Pipeline, PipelineBuilder, PipelineDefinition, PipelineContext,
    PipelineExecutor, DSLParser, AtomRegistry, parse, execute
)
from dsl.atoms.implementations import *  # Register all atoms


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def colorize(text: str, color: str) -> str:
    """Add color to text if terminal supports it"""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.ENDC}"
    return text


def print_header():
    """Print CLI header"""
    header = """
╔═══════════════════════════════════════════════════════════════╗
║             ANALYTICA DSL - Pipeline Runner                   ║
║                    Version 2.0.0                              ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(colorize(header, Colors.CYAN))


def cmd_run(args):
    """Run inline DSL pipeline"""
    pipeline_str = args.pipeline
    
    # Read from stdin if pipeline is '-'
    if pipeline_str == '-':
        pipeline_str = sys.stdin.read().strip()
    
    # Parse variables
    variables = {}
    if args.var:
        for var in args.var:
            if '=' in var:
                key, value = var.split('=', 1)
                # Try to parse as JSON, otherwise keep as string
                try:
                    variables[key] = json.loads(value)
                except:
                    variables[key] = value
    
    # Read input data if provided
    input_data = None
    if args.input:
        with open(args.input) as f:
            input_data = json.load(f)
    elif not sys.stdin.isatty() and pipeline_str != '-':
        # Read from stdin
        try:
            input_data = json.loads(sys.stdin.read())
        except:
            pass
    
    # Create context
    ctx = PipelineContext(
        variables=variables,
        domain=args.domain
    )
    
    if input_data:
        ctx.set_data(input_data)
    
    try:
        # Parse and execute
        if args.verbose:
            print(colorize(f"Parsing: {pipeline_str[:100]}...", Colors.BLUE))
        
        pipeline = parse(pipeline_str)
        
        if args.verbose:
            print(colorize(f"Pipeline: {pipeline.name}", Colors.BLUE))
            print(colorize(f"Steps: {len(pipeline.steps)}", Colors.BLUE))
        
        result = execute(pipeline, ctx)
        
        # Output result
        output_result(result, args.output)
        
    except SyntaxError as e:
        print(colorize(f"Syntax Error: {e}", Colors.RED), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(colorize(f"Error: {e}", Colors.RED), file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_exec(args):
    """Execute pipeline from file"""
    filepath = Path(args.file)
    
    if not filepath.exists():
        print(colorize(f"File not found: {filepath}", Colors.RED), file=sys.stderr)
        sys.exit(1)
    
    # Read pipeline file
    content = filepath.read_text()
    
    # Determine format
    if filepath.suffix in ('.yaml', '.yml'):
        # YAML pipeline definition
        data = yaml.safe_load(content)
        pipeline = PipelineDefinition(
            name=data.get('name', filepath.stem),
            steps=[],  # Would need to parse steps from YAML
            variables=data.get('variables', {})
        )
    elif filepath.suffix == '.json':
        # JSON pipeline definition
        data = json.loads(content)
        # Convert to pipeline definition
        pipeline = parse(data.get('dsl', ''))
    else:
        # DSL text file (.pipe, .dsl, .txt)
        pipeline = parse(content)
    
    # Merge variables from command line
    variables = dict(pipeline.variables)
    if args.var:
        for var in args.var:
            if '=' in var:
                key, value = var.split('=', 1)
                try:
                    variables[key] = json.loads(value)
                except:
                    variables[key] = value
    
    # Create context and execute
    ctx = PipelineContext(variables=variables, domain=args.domain)
    
    try:
        result = execute(pipeline, ctx)
        output_result(result, args.output)
    except Exception as e:
        print(colorize(f"Error: {e}", Colors.RED), file=sys.stderr)
        sys.exit(1)


def cmd_validate(args):
    """Validate pipeline syntax"""
    filepath = Path(args.file)
    
    if not filepath.exists():
        print(colorize(f"File not found: {filepath}", Colors.RED), file=sys.stderr)
        sys.exit(1)
    
    content = filepath.read_text()
    
    try:
        pipeline = parse(content)
        print(colorize("✓ Pipeline syntax is valid", Colors.GREEN))
        print(f"\nPipeline: {pipeline.name}")
        print(f"Steps: {len(pipeline.steps)}")
        print(f"Variables: {list(pipeline.variables.keys())}")
        
        # Show DSL representation
        if args.verbose:
            print(f"\nDSL:\n{pipeline.to_dsl()}")
        
    except SyntaxError as e:
        print(colorize(f"✗ Syntax Error: {e}", Colors.RED))
        sys.exit(1)


def cmd_list_atoms(args):
    """List all available atoms"""
    print_header()
    print(colorize("Available Atoms:", Colors.BOLD))
    print()
    
    atoms = AtomRegistry.list_atoms()
    
    for atom_type, actions in sorted(atoms.items()):
        print(colorize(f"  {atom_type}:", Colors.CYAN))
        for action in sorted(actions):
            print(f"    .{action}()")
    
    print()
    print(colorize("Usage:", Colors.BOLD))
    print("  atom_type.action(param1=value1, param2=value2)")
    print()
    print(colorize("Example:", Colors.BOLD))
    print('  data.load("sales.csv") | transform.filter(year=2024) | metrics.sum("amount")')


def cmd_build(args):
    """Interactive pipeline builder"""
    print_header()
    print(colorize("Interactive Pipeline Builder", Colors.BOLD))
    print("Type 'help' for commands, 'done' to execute, 'quit' to exit\n")
    
    steps = []
    variables = {}
    
    while True:
        try:
            line = input(colorize("pipe> ", Colors.GREEN)).strip()
        except EOFError:
            break
        
        if not line:
            continue
        
        if line == 'quit' or line == 'exit':
            break
        
        if line == 'help':
            print("""
Commands:
  help              Show this help
  atoms             List available atoms
  show              Show current pipeline
  clear             Clear pipeline
  var NAME=VALUE    Set variable
  done              Execute pipeline
  quit              Exit builder
  
Add steps by typing: atom.action(params)
Example: data.load("sales.csv")
""")
            continue
        
        if line == 'atoms':
            atoms = AtomRegistry.list_atoms()
            for atom_type, actions in sorted(atoms.items()):
                print(f"  {atom_type}: {', '.join(actions)}")
            continue
        
        if line == 'show':
            if steps:
                print(" | ".join(steps))
            else:
                print("(empty pipeline)")
            continue
        
        if line == 'clear':
            steps = []
            variables = {}
            print("Pipeline cleared")
            continue
        
        if line.startswith('var '):
            var_def = line[4:]
            if '=' in var_def:
                key, value = var_def.split('=', 1)
                variables[key.strip()] = value.strip()
                print(f"Set ${key.strip()} = {value.strip()}")
            continue
        
        if line == 'done':
            if not steps:
                print("No steps to execute")
                continue
            
            pipeline_str = " | ".join(steps)
            print(colorize(f"\nExecuting: {pipeline_str}", Colors.BLUE))
            
            try:
                ctx = PipelineContext(variables=variables)
                result = execute(pipeline_str, ctx)
                print(colorize("\nResult:", Colors.GREEN))
                print(json.dumps(result.get_data(), indent=2, default=str))
            except Exception as e:
                print(colorize(f"Error: {e}", Colors.RED))
            
            continue
        
        # Add step
        steps.append(line)
        print(f"Added: {line}")


def cmd_serve(args):
    """Start API server"""
    print_header()
    print(colorize(f"Starting API server on port {args.port}...", Colors.GREEN))
    
    # Import uvicorn and start server
    try:
        import uvicorn
        from dsl.api.server import app
        
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    except ImportError:
        print(colorize("Error: uvicorn not installed. Run: pip install uvicorn", Colors.RED))
        sys.exit(1)


def cmd_convert(args):
    """Convert between pipeline formats"""
    filepath = Path(args.file)
    
    if not filepath.exists():
        print(colorize(f"File not found: {filepath}", Colors.RED), file=sys.stderr)
        sys.exit(1)
    
    content = filepath.read_text()
    
    # Parse input
    if filepath.suffix in ('.yaml', '.yml'):
        data = yaml.safe_load(content)
        # Convert YAML to pipeline
        dsl_str = data.get('dsl', '')
        pipeline = parse(dsl_str) if dsl_str else None
    elif filepath.suffix == '.json':
        data = json.loads(content)
        pipeline = parse(data.get('dsl', ''))
    else:
        pipeline = parse(content)
    
    if not pipeline:
        print(colorize("Could not parse pipeline", Colors.RED))
        sys.exit(1)
    
    # Output in requested format
    if args.format == 'dsl':
        print(pipeline.to_dsl())
    elif args.format == 'json':
        print(json.dumps(pipeline.to_dict(), indent=2))
    elif args.format == 'yaml':
        print(pipeline.to_yaml())


def output_result(ctx: PipelineContext, format: str):
    """Output result in specified format"""
    data = ctx.get_data()
    
    if format == 'json':
        print(json.dumps(data, indent=2, default=str))
    elif format == 'yaml':
        print(yaml.dump(data, default_flow_style=False))
    elif format == 'raw':
        print(data)
    elif format == 'pretty':
        print(colorize("Result:", Colors.GREEN))
        print(json.dumps(data, indent=2, default=str))
        
        if ctx.logs:
            print(colorize("\nLogs:", Colors.BLUE))
            for log in ctx.logs:
                print(f"  [{log['level']}] {log['message']}")
        
        if ctx.errors:
            print(colorize("\nErrors:", Colors.RED))
            for err in ctx.errors:
                print(f"  {err}")
    else:
        # Default: pretty for TTY, JSON otherwise
        if sys.stdout.isatty():
            output_result(ctx, 'pretty')
        else:
            output_result(ctx, 'json')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='ANALYTICA DSL - Pipeline Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run 'data.load("sales.csv") | metrics.sum("amount")'
  %(prog)s exec monthly_report.pipe --var year=2024
  %(prog)s list-atoms
  %(prog)s serve --port 8080
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version='ANALYTICA DSL 2.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run inline DSL pipeline')
    run_parser.add_argument('pipeline', help='DSL pipeline string (use - for stdin)')
    run_parser.add_argument('--var', '-V', action='append', help='Set variable (NAME=VALUE)')
    run_parser.add_argument('--input', '-i', help='Input JSON file')
    run_parser.add_argument('--output', '-o', choices=['json', 'yaml', 'raw', 'pretty'], 
                          default='auto', help='Output format')
    run_parser.add_argument('--domain', '-d', help='Domain context')
    run_parser.set_defaults(func=cmd_run)
    
    # Exec command
    exec_parser = subparsers.add_parser('exec', help='Execute pipeline from file')
    exec_parser.add_argument('file', help='Pipeline file (.pipe, .dsl, .yaml, .json)')
    exec_parser.add_argument('--var', '-V', action='append', help='Set variable (NAME=VALUE)')
    exec_parser.add_argument('--output', '-o', choices=['json', 'yaml', 'raw', 'pretty'],
                           default='auto', help='Output format')
    exec_parser.add_argument('--domain', '-d', help='Domain context')
    exec_parser.set_defaults(func=cmd_exec)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate pipeline syntax')
    validate_parser.add_argument('file', help='Pipeline file to validate')
    validate_parser.set_defaults(func=cmd_validate)
    
    # List atoms command
    list_parser = subparsers.add_parser('list-atoms', help='List available atoms')
    list_parser.set_defaults(func=cmd_list_atoms)
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Interactive pipeline builder')
    build_parser.set_defaults(func=cmd_build)
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start API server')
    serve_parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    serve_parser.add_argument('--port', '-p', type=int, default=8080, help='Port to listen on')
    serve_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    serve_parser.set_defaults(func=cmd_serve)
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between formats')
    convert_parser.add_argument('file', help='Input file')
    convert_parser.add_argument('--format', '-f', choices=['dsl', 'json', 'yaml'],
                               default='json', help='Output format')
    convert_parser.set_defaults(func=cmd_convert)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()
