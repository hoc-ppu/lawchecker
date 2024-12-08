// Replace both backslashes and forward slashes with
// `Word Break Opportunity` tag followed by the slash

const addWordBreaksToPath = (input: string): string => {
  return input.replace(/[\\/]/g, "<wbr/>$&");
};

export default addWordBreaksToPath;
