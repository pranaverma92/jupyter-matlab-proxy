classdef TestCompleteFunction < matlab.unittest.TestCase
    % TestCompleteFunction contains unit tests for the complete function
    
    methods (TestClassSetup)
        function addFunctionPath(testCase)
            addpath('../../src/jupyter_matlab_kernel/matlab')
            addpath('../../tests/matlab-tests/')
        end
    end

    methods (TestClassTeardown)
        function removeFunctionPath(testCase)
            rmpath('../../src/jupyter_matlab_kernel/matlab')
            rmpath('../../tests/matlab-tests/')
        end
    end
    
    methods (Test)
        function testBasicCompletion(testCase)
            % Test basic completion functionality
            code = 'plo';
            cursorPosition = 2;
            result = jupyter.complete(code, cursorPosition);
            expectedMatches = 'plot';            
            testCase.verifyTrue(ismember(expectedMatches, result.matches), "Completion 'plot' was not found in the result");
        end

        function testEmptyCode(testCase)
            % Test behavior with empty code string
            code = '';
            cursorPosition = 0;
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
        end

        function testInvalidCursorPosition(testCase)
            % Test behavior with an invalid cursor position
            code = 'plot';
            cursorPosition = -1; % Invalid cursor position
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
        end
    end
end