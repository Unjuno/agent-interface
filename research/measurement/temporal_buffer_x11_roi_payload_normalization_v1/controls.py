from runner import normalize_image_data,EXPECTED_FRAME_BYTES

def expect_fail(x,exc):
    try: normalize_image_data(x)
    except exc:return True
    raise AssertionError(('accepted',type(x).__name__))

def main():
    n=0
    b=bytes([i%256 for i in range(EXPECTED_FRAME_BYTES)])
    assert normalize_image_data(b) is b; n+=1
    assert normalize_image_data(bytearray(b))==b; n+=1
    assert normalize_image_data(memoryview(b))==b; n+=1
    s=b.decode('latin-1'); assert normalize_image_data(s)==b; n+=1
    assert expect_fail('€'*(EXPECTED_FRAME_BYTES),ValueError); n+=1
    assert expect_fail(123,TypeError); n+=1
    assert expect_fail(b[:-1],ValueError); n+=1
    print('controls',n)
if __name__=='__main__':main()
