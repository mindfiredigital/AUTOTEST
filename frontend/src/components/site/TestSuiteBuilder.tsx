// Re-exports from the refactored TestSuite module.
// All logic, components, and types have been moved to ./TestSuite/
import TestSuiteBuilder from './TestSuite/index'
export default TestSuiteBuilder
export type { TestSuiteBuilderProps } from './TestSuite/types'
