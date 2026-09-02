import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScreenerPage } from './screener-page';

describe('ScreenerPage', () => {
  let component: ScreenerPage;
  let fixture: ComponentFixture<ScreenerPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScreenerPage],
    }).compileComponents();

    fixture = TestBed.createComponent(ScreenerPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
