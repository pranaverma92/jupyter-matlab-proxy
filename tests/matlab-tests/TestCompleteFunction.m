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
            disp("result.matches")
            disp(size(result.matches))
            disp("result.matches end")
            testCase.verifyTrue(isempty(result.matches));
        end

        function testInvalidCursorPosition(testCase)
            % Test behavior with an invalid cursor position
            code = 'plot';
            cursorPosition = -1; % Invalid cursor position
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
        end

        function testReturnExceptionOnReset(testCase)
            % Test that an exception can be returned and reset
            testMessage = 'Test Exception';
            jupyter.getOrStashExceptions(testMessage, false); % Stash the exception without the intention to reset
            result = jupyter.getOrStashExceptions([], true); % Retrieve and reset
            testCase.assertEqual(result, testMessage, ...
                'The function should return the Test Exception when resetFlag is true.');
            resultAfterReset = jupyter.getOrStashExceptions();
            testCase.assertEmpty(resultAfterReset, ...
                'The stashed exception should be cleared after being reset.');
        end

        function testReturnStashedExceptionWithoutReset(testCase)
            % Test that the stashed exception is returned without resetting
            testMessage = 'Test Exception';
            jupyter.getOrStashExceptions(testMessage); % Stash the exception
            result = jupyter.getOrStashExceptions(); % Retrieve without resetting
            testCase.assertEqual(result, testMessage);
        end


    end
end